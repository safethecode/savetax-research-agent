"""Read-only SaveTax transport with narrow credential destinations.

Credentials stay in memory and Authorization headers. No redirect is followed,
including redirects between allowed hosts. Exceptions deliberately omit response
bodies, request objects, headers, and untrusted server messages.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import socket
import ssl
import tempfile
from typing import Any
from urllib.parse import parse_qsl, unquote, urlsplit
import zipfile

import requests


DATASET_URL = "https://savetax-dataset.reform-dev-infra.workers.dev/latest/savetax-products.zip"
API_HOSTS = frozenset({"api.savetax.now", "hackathon.savetax.now"})
TOKEN_PATTERN = re.compile(r"savetax_[A-Za-z0-9_-]{20,}")
SENSITIVE_KEYS = frozenset({"authorization", "token", "pat", "access_token", "savetax_token"})


class SaveTaxError(RuntimeError):
    """Sanitized failure; inspect status/code/stage rather than server text."""

    def __init__(self, message: str, *, status: int | None = None,
                 code: str | None = None, stage: str = "validation",
                 retry_after: int | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.stage = stage
        self.retry_after = retry_after


class UnsafeUrlError(SaveTaxError):
    """The destination or query is unsuitable for credentialed GET."""


def _redact(value: Any, token: str) -> Any:
    if isinstance(value, str):
        return TOKEN_PATTERN.sub("[REDACTED]", value.replace(token, "[REDACTED]"))
    if isinstance(value, list):
        return [_redact(part, token) for part in value]
    if isinstance(value, dict):
        return {
            _redact(key, token): "[REDACTED]" if str(key).lower() in SENSITIVE_KEYS else _redact(part, token)
            for key, part in value.items()
        }
    return value


def _validate_url(url: str, params: dict | None = None) -> None:
    """Validate the raw URL before requests can normalize or transmit it."""
    unsafe = not isinstance(url, str) or any(ord(c) < 33 for c in url)
    parsed = None
    try:
        parsed = urlsplit(url)
        decoded = unquote(parsed.path)
        unsafe = unsafe or parsed.scheme != "https" or bool(parsed.fragment)
        unsafe = unsafe or "\\" in decoded or "//" in decoded
        unsafe = unsafe or any(part in {".", ".."} for part in decoded.split("/"))
        api = parsed.netloc in API_HOSTS and parsed.path.startswith("/v1/")
        unsafe = unsafe or not (api or url == DATASET_URL)
        query = parse_qsl(parsed.query, keep_blank_values=True)
        if params:
            query += [(str(key), str(value)) for key, value in params.items()]
        unsafe = unsafe or bool(TOKEN_PATTERN.search(url))
        unsafe = unsafe or any(key.lower() in SENSITIVE_KEYS or TOKEN_PATTERN.search(value) for key, value in query)
    except (ValueError, TypeError):
        unsafe = True
    if unsafe:
        raise UnsafeUrlError("Credentialed GET destination or query rejected")


class SaveTaxClient:
    """Only GETs the two /v1/ APIs and the exact official dataset ZIP."""

    def __init__(self, token: str | None = None, guide_path: str | Path | None = None,
                 timeout: float = 30):
        if token is None:
            token = os.environ.get("SAVETAX_TOKEN")
            if not token:
                path = Path(guide_path) if guide_path is not None else Path.cwd() / "savetax-agent-guide.md"
                if guide_path is None and not path.exists():
                    path = Path.cwd() / "guide.md"
                try:
                    text = path.read_text(encoding="utf-8-sig").replace("\\_", "_")
                    matches = set(TOKEN_PATTERN.findall(text))
                except (OSError, UnicodeError):
                    matches = set()
                token = matches.pop() if len(matches) == 1 else None
        if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
            raise SaveTaxError("One valid SaveTax credential is required", code="credential_unavailable")
        if timeout <= 0:
            raise SaveTaxError("Timeout must be positive")
        self._token = token
        self.timeout = timeout

    def __repr__(self) -> str:
        return f"SaveTaxClient(timeout={self.timeout!r}, credential=[REDACTED])"

    def _get(self, url: str, params: dict | None = None, *, stream: bool = False) -> requests.Response:
        _validate_url(url, params)
        error = None
        try:
            response = requests.get(
                url, params=params,
                headers={"Authorization": "Bearer " + self._token,
                         "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                timeout=self.timeout, allow_redirects=False, stream=stream,
            )
        except requests.RequestException as exc:
            error = SaveTaxError("SaveTax transport failed (" + type(exc).__name__ + ")",
                                 code=type(exc).__name__, stage="transport")
        if error is not None:
            raise error from None
        if response.status_code < 200 or response.status_code >= 300:
            status = response.status_code
            code = "redirect_blocked" if 300 <= status < 400 else "http_error"
            try:
                body = response.json()
                detail = body.get("error", body) if isinstance(body, dict) else {}
                candidate = detail.get("code") if isinstance(detail, dict) else None
                if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", candidate) and not TOKEN_PATTERN.search(candidate):
                    code = candidate
            except (ValueError, TypeError):
                pass
            retry = response.headers.get("Retry-After", "")
            retry_after = int(retry) if retry.isdecimal() and len(retry) <= 8 else None
            response.close()
            raise SaveTaxError(f"SaveTax HTTP {status} ({code})", status=status, code=code,
                               stage="http", retry_after=retry_after)
        return response

    def get_json(self, url: str, params: dict | None = None) -> dict:
        response = self._get(url, params)
        error = None
        value = None
        try:
            value = response.json()
            if not isinstance(value, dict):
                error = SaveTaxError("SaveTax JSON object expected", stage="decode")
        except (ValueError, TypeError):
            error = SaveTaxError("SaveTax JSON decoding failed", stage="decode")
        finally:
            response.close()
        if error is not None:
            raise error from None
        return _redact(value, self._token)

    def download_dataset(self, destination: str | Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = self._get(DATASET_URL, stream=True)
        partial = None
        error = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".savetax-", suffix=".part", dir=destination.parent, delete=False) as output:
                partial = Path(output.name)
                for block in response.iter_content(chunk_size=1024 * 1024):
                    if block:
                        output.write(block)
            if not zipfile.is_zipfile(partial):
                error = SaveTaxError("Dataset response is not a ZIP archive", stage="decode")
            else:
                partial.replace(destination)
        except requests.RequestException:
            error = SaveTaxError("Dataset stream failed", stage="transport")
        except OSError:
            error = SaveTaxError("Dataset could not be saved", stage="filesystem")
        finally:
            response.close()
            if partial is not None:
                partial.unlink(missing_ok=True)
        if error is not None:
            raise error from None
        return destination


def diagnose_connection(host: str, *, timeout: float = 5) -> dict:
    """Unauthenticated DNS and TCP/TLS probes; no credentials or HTTP request.

    HTTP status is intentionally taken from an actual GET, never inferred from
    DNS/TLS. This helps distinguish host resolution, policy, and server failures.
    """
    if host not in API_HOSTS | {"savetax-dataset.reform-dev-infra.workers.dev"}:
        raise UnsafeUrlError("Diagnostic host rejected")
    result = {"host": host, "dns": "unattempted", "tcp_tls": "unattempted", "http": "unattempted"}
    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        result["dns"] = "ok"
    except socket.gaierror:
        result["dns"] = "failed"
        return result
    except PermissionError:
        result["dns"] = "environment_policy_denied"
        return result
    try:
        with socket.create_connection((host, 443), timeout=timeout) as transport:
            with ssl.create_default_context().wrap_socket(transport, server_hostname=host):
                result["tcp_tls"] = "ok"
    except PermissionError:
        result["tcp_tls"] = "environment_policy_denied"
    except (OSError, ssl.SSLError):
        result["tcp_tls"] = "failed"
    return result
