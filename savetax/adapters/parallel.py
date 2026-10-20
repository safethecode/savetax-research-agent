"""Read-only Parallel Search v1 adapter with a fixed credential destination.

The search service uses POST for reads. Returned snippets are discovery data,
not verified retailer prices. No search-result URL is fetched by this module.
"""
from __future__ import annotations

import math
import os
import re
from urllib.parse import parse_qsl, unquote, urlsplit

import requests
from requests.auth import AuthBase


SEARCH_URL = 'https://api.parallel.ai/v1/search'
_PAT = re.compile(r'savetax_[A-Za-z0-9_-]{20,}')
_SENSITIVE_QUERY_KEYS = frozenset({
    'authorization', 'token', 'pat', 'access_token', 'api_key', 'apikey',
    'x-api-key', 'key', 'client_secret', 'savetax_token',
})


class ParallelError(RuntimeError):
    """A fixed error code; never retains server text or request objects."""

    def __init__(self, code: str, *, status: int | None = None,
                 stage: str = 'validation', retry_after: int | None = None):
        super().__init__('parallel: ' + code)
        self.code = code
        self.status = status
        self.stage = stage
        self.retry_after = retry_after


class _NoImplicitCredentials(AuthBase):
    """Prevent requests from attaching .netrc Basic Authorization."""

    def __call__(self, request):
        request.headers.pop('Authorization', None)
        return request


class ParallelClient:
    """Only searches https://api.parallel.ai/v1/search; never auto-retries."""

    def __init__(self, api_key: str | None = None, timeout: float = 30):
        key = api_key if api_key is not None else os.environ.get('PARALLEL_API_KEY')
        if not isinstance(key, str) or not key or any(ord(c) < 33 or ord(c) > 126 for c in key):
            raise ParallelError('credential_unavailable')
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or timeout <= 0):
            raise ParallelError('invalid_timeout')
        self._api_key = key
        self._secrets = tuple(sorted({key, *(value for name, value in os.environ.items()
            if name.endswith('_API_KEY') and value)}, key=len, reverse=True))
        self.timeout = timeout

    def __repr__(self):
        return f'ParallelClient(timeout={self.timeout!r}, credential=[REDACTED])'

    def _has_secret(self, text: str) -> bool:
        return bool(_PAT.search(text)) or any(secret in text for secret in self._secrets)

    def _redact(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, '[REDACTED]')
        return _PAT.sub('[REDACTED]', text)

    def _source_url(self, value) -> str | None:
        if not isinstance(value, str) or not value or len(value) > 8192:
            return None
        try:
            decoded = unquote(value)
            parts = urlsplit(value)
            if (parts.scheme != 'https' or not parts.hostname or parts.username
                    or parts.password or parts.fragment or '\\' in decoded
                    or any(ord(c) < 33 for c in decoded) or self._has_secret(decoded)):
                return None
            if any(name.lower() in _SENSITIVE_QUERY_KEYS for name, _ in parse_qsl(parts.query)):
                return None
        except (ValueError, TypeError):
            return None
        return value

    def search(self, query: str | None = None, *, objective: str | None = None,
               max_results: int = 5) -> dict:
        """Return at most 10 source_url/title/excerpt records from one search.

        v1 has no max_results request field; the result limit is applied locally.
        At least one query is required by v1, so objective-only calls reuse it.
        """
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 10:
            raise ParallelError('invalid_max_results')
        for value in [query, objective]:
            if value is not None and (not isinstance(value, str) or not value.strip()
                    or len(value) > 10000 or any(ord(c) < 32 for c in value)
                    or self._has_secret(value) or self._has_secret(unquote(value))):
                raise ParallelError('invalid_search_input')
        if query is None and objective is None:
            raise ParallelError('invalid_search_input')
        search_query = (query if query is not None else objective).strip()
        payload = {'search_queries': [search_query], 'mode': 'fast', 'max_chars_total': 8000}
        if objective is not None:
            payload['objective'] = objective.strip()
        failed = False
        try:
            response = requests.post(SEARCH_URL, json=payload,
                headers={'x-api-key': self._api_key, 'Content-Type': 'application/json',
                         'Accept': 'application/json', 'User-Agent': 'savetax-research/0.1'},
                auth=_NoImplicitCredentials(), timeout=self.timeout, allow_redirects=False)
        except requests.RequestException:
            failed = True
        if failed:
            raise ParallelError('transport_error', stage='transport') from None
        status = response.status_code
        if not 200 <= status < 300:
            retry = response.headers.get('Retry-After', '')
            retry_after = int(retry) if retry.isdecimal() and len(retry) <= 8 else None
            response.close()
            code = ('redirect_blocked' if 300 <= status < 400 else
                    'rate_limited' if status == 429 else 'http_error')
            raise ParallelError(code, status=status, stage='http', retry_after=retry_after)
        value = None
        try:
            value = response.json()
        except (ValueError, TypeError):
            failed = True
        finally:
            response.close()
        if failed or not isinstance(value, dict) or not isinstance(value.get('results'), list):
            raise ParallelError('invalid_response', stage='decode')
        results = []
        for row in value['results']:
            if (not isinstance(row, dict) or not isinstance(row.get('title'), str)
                    or not isinstance(row.get('excerpts'), list)
                    or not all(isinstance(part, str) for part in row['excerpts'])):
                raise ParallelError('invalid_response', stage='decode')
            url = self._source_url(row.get('url'))
            if url is not None and len(results) < max_results:
                results.append({'source_url': url, 'title': self._redact(row['title'])[:1000],
                    'excerpt': self._redact('\n'.join(row['excerpts']))[:8000]})
        search_id = value.get('search_id')
        return {'provider': 'parallel',
                'search_id': self._redact(search_id)[:200] if isinstance(search_id, str) else None,
                'query': search_query, 'results': results}
