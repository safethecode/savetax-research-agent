"""Compatibility exports; implementation lives in savetax.adapters.reports."""
from .adapters.reports import (
    re,
    requests,
    SaveTaxClient,
    SaveTaxError,
    TOKEN_PATTERN,
    _redact,
    _source_valid,
    REPORTS_URL,
    LIMITS,
    validate_report,
    ReportClient,
)

__all__ = ['re', 'requests', 'SaveTaxClient', 'SaveTaxError', 'TOKEN_PATTERN', 'REPORTS_URL', 'LIMITS', 'validate_report', 'ReportClient']
