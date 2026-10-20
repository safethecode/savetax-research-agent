"""Compatibility exports; implementation lives in savetax.adapters.datasets."""
from .adapters.datasets import (
    Decimal,
    Path,
    duckdb,
    DatasetError,
    REQUIRED,
    _open,
    _number,
    dataset_summary,
    mine_batch,
)

__all__ = ['Decimal', 'Path', 'duckdb', 'DatasetError', 'REQUIRED', 'dataset_summary', 'mine_batch']
