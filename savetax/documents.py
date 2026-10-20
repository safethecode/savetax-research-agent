"""Compatibility exports; implementation lives in savetax.adapters.documents."""
from .adapters.documents import (
    datetime,
    timezone,
    hashlib,
    io,
    Path,
    PurePosixPath,
    re,
    struct,
    ET,
    BadZipFile,
    ZipFile,
    zlib,
    CFB_MAGIC,
    HWPX_REVISION_MARKERS,
    HWPX_PARAGRAPH_NS,
    _xml,
    _tag,
    _xml_text,
    _read_hwpx,
    _hwp_paragraph,
    _hwp_records,
    _read_hwp,
    read_document,
)

__all__ = ['datetime', 'timezone', 'hashlib', 'io', 'Path', 'PurePosixPath', 're', 'struct', 'ET', 'BadZipFile', 'ZipFile', 'zlib', 'CFB_MAGIC', 'HWPX_REVISION_MARKERS', 'HWPX_PARAGRAPH_NS', 'read_document']
