"""Compatibility exports; implementation lives in savetax.adapters.catalog."""
from .adapters.catalog import (
    os,
    Path,
    re,
    socket,
    ssl,
    tempfile,
    Any,
    parse_qsl,
    unquote,
    urlsplit,
    zipfile,
    requests,
    DATASET_URL,
    API_HOSTS,
    TOKEN_PATTERN,
    SENSITIVE_KEYS,
    SaveTaxError,
    UnsafeUrlError,
    _redact,
    _validate_url,
    SaveTaxClient,
    diagnose_connection,
)

__all__ = ['os', 'Path', 're', 'socket', 'ssl', 'tempfile', 'Any', 'parse_qsl', 'unquote', 'urlsplit', 'zipfile', 'requests', 'DATASET_URL', 'API_HOSTS', 'TOKEN_PATTERN', 'SENSITIVE_KEYS', 'SaveTaxError', 'UnsafeUrlError', 'SaveTaxClient', 'diagnose_connection']
