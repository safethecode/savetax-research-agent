"""Compatibility exports; implementation lives in savetax.runtime.secrets."""
from .runtime.secrets import (
    contextmanager,
    os,
    re,
    Path,
    ALLOWED_KEYS,
    load_env_file,
    environment,
    activated_environment,
    redact_keys,
)

__all__ = ['contextmanager', 'os', 're', 'Path', 'ALLOWED_KEYS', 'load_env_file', 'environment', 'activated_environment', 'redact_keys']
