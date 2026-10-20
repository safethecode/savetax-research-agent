"""Layered implementations remain importable and preserve legacy public APIs."""
import ast
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


IMPLEMENTATIONS = {
    'client': ('adapters.catalog', 'SaveTaxClient'),
    'analysis': ('adapters.datasets', 'mine_batch'),
    'browser': ('adapters.browser', 'BrowserRuntime'),
    'parallel': ('adapters.parallel', 'ParallelClient'),
    'market': ('adapters.market', 'MarketClient'),
    'documents': ('adapters.documents', 'read_document'),
    'reports': ('adapters.reports', 'ReportClient'),
    'counterevidence': ('adapters.counterevidence', 'CounterevidenceClient'),
    'secrets': ('runtime.secrets', 'environment'),
    'rules': ('domain.rules', 'apply_rules'),
    'queue': ('domain.queue', 'prioritize'),
    'submissions': ('adapters.scoring', 'ScoreClient'),
}


class LayerImportTests(unittest.TestCase):
    def test_all_canonical_implementations_are_available(self):
        for canonical, _ in IMPLEMENTATIONS.values():
            with self.subTest(module=canonical):
                self.assertIsNotNone(importlib.util.find_spec('savetax.' + canonical))

    def test_legacy_public_entrypoints_are_the_canonical_implementations(self):
        for legacy, (canonical, name) in IMPLEMENTATIONS.items():
            with self.subTest(module=legacy):
                old = getattr(importlib.import_module('savetax.' + legacy), name)
                current = getattr(importlib.import_module('savetax.' + canonical), name)
                self.assertIs(old, current)
                self.assertEqual(current.__module__, 'savetax.' + canonical)
        from savetax.submissions import build_submission
        from savetax.domain.scoring import build_submission as canonical_builder
        self.assertIs(build_submission, canonical_builder)

    def test_fresh_imports_enforce_layer_dependency_direction(self):
        # A fresh interpreter exercises imports even when other test modules have
        # already loaded every adapter. No transports are called by this smoke.
        script = textwrap.dedent('''
            import builtins
            import importlib
            import importlib.util

            legacy = set(LEGACY_MODULES)
            original = builtins.__import__

            def layer_import(name, globals=None, locals=None, fromlist=(), level=0):
                caller = (globals or {}).get('__name__', '')
                package = (globals or {}).get('__package__', '')
                target = importlib.util.resolve_name('.' * level + name, package) if level else name
                layered = caller.startswith(('savetax.adapters.', 'savetax.domain.',
                                             'savetax.runtime.', 'savetax.application.',
                                             'savetax.commands.'))
                if layered and target in legacy:
                    raise ImportError(caller + ' depends on legacy facade ' + target)
                if caller.startswith('savetax.domain.') and target.startswith((
                        'savetax.adapters', 'savetax.application', 'savetax.commands')):
                    raise ImportError('Domain depends on an outer layer: ' + target)
                if caller.startswith('savetax.runtime.') and target.startswith((
                        'savetax.adapters', 'savetax.domain', 'savetax.application', 'savetax.commands')):
                    raise ImportError('Runtime depends on a business layer: ' + target)
                if caller.startswith('savetax.adapters.') and target.startswith('savetax.application'):
                    if not (caller == 'savetax.adapters.scoring'
                            and target == 'savetax.application.publication'
                            and tuple(fromlist) == ('require_publication_approval',)):
                        raise ImportError('Adapter imports application: ' + caller + ' -> ' + target)
                return original(name, globals, locals, fromlist, level)

            builtins.__import__ = layer_import
            for name in CANONICAL_MODULES:
                importlib.import_module(name)
            importlib.import_module('savetax.cli')
            importlib.import_module('savetax.application.research')
            importlib.import_module('savetax.commands.research')
        ''').replace('LEGACY_MODULES', repr(['savetax.' + name for name in IMPLEMENTATIONS]))
        script = script.replace('CANONICAL_MODULES', repr([
            'savetax.' + module for module, _ in IMPLEMENTATIONS.values()]))
        result = subprocess.run([sys.executable, '-c', script],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_lazy_production_imports_also_use_canonical_modules(self):
        # Imports inside deferred tool methods must obey the same direction as
        # the eager imports exercised by the fresh-interpreter smoke above.
        package_root = Path(__file__).resolve().parents[1] / 'savetax'
        legacy = {'savetax.' + name for name in IMPLEMENTATIONS} | {'savetax.evidence'}
        paths = [package_root / 'cli.py']
        for layer in ('adapters', 'domain', 'runtime', 'application', 'commands'):
            paths.extend((package_root / layer).glob('*.py'))
        for path in paths:
            package = 'savetax' + ('.' + path.parent.name if path.parent != package_root else '')
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                target = importlib.util.resolve_name('.' * node.level + (node.module or ''), package)
                with self.subTest(module=str(path.relative_to(package_root)), line=node.lineno):
                    self.assertNotIn(target, legacy, 'Production import goes through a legacy facade')
