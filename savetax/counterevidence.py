"""Compatibility exports; implementation lives in savetax.adapters.counterevidence."""
from .adapters.counterevidence import (
    json,
    re,
    requests,
    SaveTaxClient,
    SaveTaxError,
    TOKEN_PATTERN,
    _redact,
    BASE,
    _identifier,
    _key,
    validate_counterevidence,
    CounterevidenceClient,
)

__all__ = ['json', 're', 'requests', 'SaveTaxClient', 'SaveTaxError', 'TOKEN_PATTERN', 'BASE', 'validate_counterevidence', 'CounterevidenceClient']
