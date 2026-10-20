"""Compatibility exports; implementation lives in savetax.domain.rules."""
from .domain.rules import (
    deepcopy,
    Decimal,
    InvalidOperation,
    hashlib,
    math,
    re,
    TEXT_FIELDS,
    NUMERIC_FIELDS,
    ALLOWED_FIELDS,
    OPERATORS,
    _NUMBER,
    _keys,
    _strategy_value,
    validate_strategy,
    _record_value,
    _matches,
    apply_rules,
    deterministic_batches,
    learn_from_feedback,
)

__all__ = ['deepcopy', 'Decimal', 'InvalidOperation', 'hashlib', 'math', 're', 'TEXT_FIELDS', 'NUMERIC_FIELDS', 'ALLOWED_FIELDS', 'OPERATORS', 'validate_strategy', 'apply_rules', 'deterministic_batches', 'learn_from_feedback']
