"""Compatibility exports; implementation lives in savetax.adapters.browser."""
from .adapters.browser import (
    contextmanager,
    datetime,
    timezone,
    hashlib,
    json,
    os,
    re,
    Path,
    shutil,
    subprocess,
    time,
    urlsplit,
    build_opener,
    ProxyHandler,
    _source_valid,
    environment,
    redact_keys,
    JEV_GUARD_PATTERN,
    BrowserRuntime,
)

__all__ = ['contextmanager', 'datetime', 'timezone', 'hashlib', 'json', 'os', 're', 'Path', 'shutil', 'subprocess', 'time', 'urlsplit', 'build_opener', 'ProxyHandler', 'environment', 'redact_keys', 'JEV_GUARD_PATTERN', 'BrowserRuntime']
