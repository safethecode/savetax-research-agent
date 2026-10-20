"""Compatibility exports; implementation lives in savetax.adapters.parallel."""
from .adapters.parallel import (
    math,
    os,
    re,
    parse_qsl,
    unquote,
    urlsplit,
    requests,
    AuthBase,
    SEARCH_URL,
    _PAT,
    _SENSITIVE_QUERY_KEYS,
    ParallelError,
    _NoImplicitCredentials,
    ParallelClient,
)

__all__ = ['math', 'os', 're', 'parse_qsl', 'unquote', 'urlsplit', 'requests', 'AuthBase', 'SEARCH_URL', 'ParallelError', 'ParallelClient']
