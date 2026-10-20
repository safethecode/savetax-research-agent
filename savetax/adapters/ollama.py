"""Bounded loopback-only inference; the returned object is an unapproved proposal."""
import getpass
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time

import requests

from ..runtime.artifacts import exclusive_lock
from ..runtime.config import LocalProfile


MAX_RESPONSE_BYTES = 1_048_576
MAX_PROMPT_BYTES = 131_072
MAX_SCHEMA_BYTES = 65_536


class OllamaError(RuntimeError):
    """Sanitized fixed code, never a prompt, response body, or raw HTTP error."""

    def __init__(self, code):
        self.code = code
        super().__init__('ollama: ' + code)


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _invalid_constant(_value):
    raise ValueError('nonfinite JSON number')


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('nonfinite JSON number')
    return value


def _strict_object(text):
    result = json.loads(text, object_pairs_hook=_object_pairs,
                        parse_constant=_invalid_constant, parse_float=_finite_float)
    if not isinstance(result, dict):
        raise ValueError('JSON object required')
    return result


class OllamaClient:
    def __init__(self, profile=None, *, lock_path=None):
        self.profile = profile if profile is not None else LocalProfile()
        if not isinstance(self.profile, LocalProfile):
            raise ValueError('An explicit LocalProfile is required')
        user_hash = hashlib.sha256(getpass.getuser().encode('utf-8')).hexdigest()[:16]
        self.lock_path = (Path(lock_path) if lock_path is not None else
                          Path(tempfile.gettempdir()) / ('savetax-local-' + user_hash) / 'ollama.lock')
        self.session = requests.Session()
        # No environment proxy, .netrc credentials, API key, or parent auth is used.
        self.session.trust_env = False
        self.session.auth = None
        self.session.proxies.clear()
        self.last_metadata = {}

    def generate(self, prompt, schema):
        self.last_metadata = {}
        try:
            valid_prompt = (isinstance(prompt, str) and bool(prompt.strip())
                            and '\x00' not in prompt
                            and len(prompt.encode('utf-8')) <= MAX_PROMPT_BYTES)
            encoded_schema = json.dumps(schema, ensure_ascii=False, allow_nan=False).encode('utf-8')
            if not valid_prompt or not isinstance(schema, dict) or not schema or len(encoded_schema) > MAX_SCHEMA_BYTES:
                raise ValueError
        except (ValueError, TypeError, UnicodeError):
            raise OllamaError('invalid_input') from None
        instruction = ('Return one JSON object matching this schema:\n'
                       + encoded_schema.decode('utf-8') + '\n\n' + prompt)
        if len(instruction.encode('utf-8')) > MAX_PROMPT_BYTES:
            raise OllamaError('invalid_input')
        payload = {'model': self.profile.model, 'prompt': instruction, 'format': schema,
                   'stream': False, 'think': self.profile.think,
                   'options': {'temperature': 0, 'presence_penalty': 0, 'num_ctx': self.profile.num_ctx,
                               'num_predict': self.profile.num_predict}}
        try:
            with exclusive_lock(self.lock_path):
                return self._generate(payload)
        except OllamaError:
            raise
        except (OSError, RuntimeError, ValueError):
            raise OllamaError('inference_lock_unavailable') from None

    def _generate(self, payload):
        started = time.monotonic()
        response = None
        try:
            response = self.session.post(self.profile.base_url + '/api/generate', json=payload,
                timeout=(min(10, self.profile.timeout), self.profile.timeout),
                allow_redirects=False, stream=True, proxies={}, auth=None)
            if not 200 <= response.status_code < 300:
                raise OllamaError('redirect_blocked' if 300 <= response.status_code < 400 else 'http_error')
            length = response.headers.get('Content-Length')
            if length and (not length.isdecimal() or int(length) > MAX_RESPONSE_BYTES):
                raise OllamaError('response_too_large')
            blocks, size = [], 0
            for block in response.iter_content(chunk_size=8192):
                if time.monotonic() - started >= self.profile.timeout:
                    raise OllamaError('deadline_exceeded')
                size += len(block)
                if size > MAX_RESPONSE_BYTES:
                    raise OllamaError('response_too_large')
                blocks.append(block)
            if time.monotonic() - started >= self.profile.timeout:
                raise OllamaError('deadline_exceeded')
            outer = _strict_object(b''.join(blocks).decode('utf-8'))
            if (outer.get('done') is not True or outer.get('model') != self.profile.model
                    or outer.get('done_reason') not in (None, 'stop')
                    or not isinstance(outer.get('response'), str)):
                raise OllamaError('incomplete_or_unexpected_model')
            value = _strict_object(outer['response'])
            metadata = {'provider': 'ollama', 'model': outer['model']}
            for key in ('total_duration', 'load_duration', 'prompt_eval_count',
                        'prompt_eval_duration', 'eval_count', 'eval_duration'):
                if type(outer.get(key)) is int and outer[key] >= 0:
                    metadata[key] = outer[key]
            digest = outer.get('digest')
            if isinstance(digest, str) and len(digest) <= 100:
                metadata['digest'] = digest
            self.last_metadata = metadata
            return value
        except OllamaError:
            raise
        except requests.RequestException:
            raise OllamaError('transport_error') from None
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise OllamaError('invalid_response') from None
        finally:
            if response is not None:
                response.close()
