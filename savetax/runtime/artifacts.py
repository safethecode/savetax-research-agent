"""JSON artifacts and cooperative filesystem locks, without business decisions."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import stat
import tempfile


def _canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def canonical_hash(value):
    """Hash strict, sorted-key UTF-8 JSON without changing decimal strings."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _reject_links(path):
    # Check lexical components before resolve() can hide a symlink or junction.
    for part in (*reversed(path.parents), path):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
                getattr(info, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
            raise ValueError('Artifact paths cannot contain symbolic links or reparse points')


def safe_path(root, relative):
    """Resolve a portable relative artifact path inside root, rejecting links."""
    text = relative.as_posix() if isinstance(relative, Path) else os.fspath(relative)
    if (not isinstance(text, str) or not text or '\x00' in text
            or '\\' in text or ':' in text
            or Path(text).is_absolute() or PureWindowsPath(text).drive
            or any(part in ('', '.', '..') for part in text.split('/'))):
        raise ValueError('An artifact must use a nonempty safe relative path')
    base = Path(root).absolute()
    target = base.joinpath(*text.split('/'))
    _reject_links(base)
    _reject_links(target)
    base = base.resolve()
    target = target.resolve()
    if not target.is_relative_to(base):
        raise ValueError('Artifact path escapes its root')
    return target


def atomic_json(path, value):
    """Replace one JSON artifact only after its complete UTF-8 write succeeds."""
    data = _canonical_bytes(value) + b'\n'
    target = Path(path).absolute()
    _reject_links(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    _reject_links(target)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.' + target.name + '-', suffix='.tmp',
                                         dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def exclusive_lock(path):
    """Fail instead of overlapping work; stale locks need explicit inspection."""
    target = Path(path).absolute()
    _reject_links(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    _reject_links(target)
    try:
        handle = target.open('x', encoding='utf-8')
    except FileExistsError:
        raise RuntimeError('Another operation owns this filesystem lock') from None
    owned = os.fstat(handle.fileno())
    try:
        with handle:
            handle.write(json.dumps({'pid': os.getpid()}))
        yield target
    finally:
        try:
            current = target.lstat()
        except FileNotFoundError:
            pass
        else:
            if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                target.unlink(missing_ok=True)
