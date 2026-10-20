import hashlib
import json
import os
from pathlib import Path
import tempfile
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from savetax.runtime.artifacts import atomic_json, canonical_hash, exclusive_lock, safe_path
from savetax.runtime.config import LocalProfile


class LocalRuntimeTests(unittest.TestCase):
    def test_hash_uses_ordered_utf8_json_and_rejects_nonfinite_numbers(self):
        self.assertEqual(canonical_hash({'z': '한글', 'a': '1'}),
                         hashlib.sha256('{"a":"1","z":"한글"}'.encode()).hexdigest())
        for number in (float('nan'), float('inf')):
            with self.subTest(number=number), self.assertRaises(ValueError):
                canonical_hash({'amount': number})

    def test_atomic_json_preserves_original_on_failed_replace_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'nested' / 'record.json'
            atomic_json(target, {'old': True})
            with patch('pathlib.Path.replace', side_effect=OSError('disk unavailable')):
                with self.assertRaises(OSError):
                    atomic_json(target, {'new': True})
            self.assertEqual(json.loads(target.read_text(encoding='utf-8')), {'old': True})
            self.assertEqual(list(target.parent.iterdir()), [target])
            atomic_json(target, {'new': '한글'})
            self.assertEqual(json.loads(target.read_text(encoding='utf-8')), {'new': '한글'})

    def test_relative_paths_cannot_escape_or_reference_windows_drives_and_streams(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(safe_path(root, 'sources/item.json'), root / 'sources' / 'item.json')
            self.assertEqual(safe_path(root, Path('sources') / 'item.json'), root / 'sources' / 'item.json')
            for path in ('../outside', 'a/../../outside', '/absolute', 'C:\\outside',
                         'C:outside', '\\\\host\\share', 'a\\..\\outside', 'x:stream', '', 'x\x00y'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    safe_path(root, path)

    def test_relative_path_and_atomic_write_reject_symlink_components(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            actual = root / 'actual'
            actual.mkdir()
            link = root / 'link'
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('symlink creation unavailable on this host')
            with self.assertRaises(ValueError):
                safe_path(root, 'link/source.json')
            with self.assertRaises(ValueError):
                atomic_json(link / 'source.json', {'x': 1})

    def test_lock_excludes_nested_owner_and_is_released_after_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'locks' / 'run.lock'
            with self.assertRaisesRegex(RuntimeError, 'test failure'):
                with exclusive_lock(path):
                    self.assertTrue(path.exists())
                    with self.assertRaises(RuntimeError):
                        with exclusive_lock(path):
                            self.fail('concurrent owner acquired lock')
                    raise RuntimeError('test failure')
            self.assertFalse(path.exists())
            with exclusive_lock(path):
                pass

    def test_windows_reparse_component_is_rejected_without_symlink_privilege(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path.lstat
            def observed(path):
                if path.name == 'junction':
                    return SimpleNamespace(st_mode=stat.S_IFDIR,
                                           st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
                return original(path)
            with patch('pathlib.Path.lstat', observed), self.assertRaises(ValueError):
                safe_path(folder, 'junction/source.json')

    def test_replaced_lock_is_not_removed_by_its_previous_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'operation.lock'
            with exclusive_lock(path):
                replacement = path.with_suffix('.replacement')
                replacement.write_text('another owner', encoding='utf-8')
                replacement.replace(path)
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding='utf-8'), 'another owner')

    def test_local_profile_rejects_non_loopback_credentials_and_invalid_limits(self):
        profile = LocalProfile()
        self.assertEqual(profile.as_dict(), {
            'model': 'qwen3.5:9b', 'base_url': 'http://127.0.0.1:11434',
            'timeout': 180, 'num_ctx': 8192, 'num_predict': 1536, 'think': False})
        for url in ('https://example.com', 'http://localhost:11434', 'http://127.0.0.1.evil',
                    'http://user:password@127.0.0.1:11434', 'http://127.0.0.1:11434/api',
                    'http://127.0.0.1:11434?key=x', 'http://0.0.0.0:11434',
                    'http://127.0.0.1:0', 'http://127.0.0.1:11434#fragment',
                    'http://127.0.0.1:11434?', 'http://127.0.0.1:11434#'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                LocalProfile(base_url=url)
        self.assertEqual(LocalProfile(base_url='http://[::1]:11434/').base_url, 'http://[::1]:11434')
        for options in ({'timeout': 0}, {'timeout': float('nan')}, {'timeout': True},
                        {'num_ctx': 0}, {'num_predict': -1}, {'num_predict': True},
                        {'think': 'false'}, {'model': ''}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                LocalProfile(**options)
