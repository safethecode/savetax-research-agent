"""Explicit cloud Codex evidence review using bounded ordinary ``codex exec``.

No local fallback, shell, vendor credentials or source-provided tool code is used.
Read-only is a CLI execution policy, not an OS-wide filesystem/network sandbox.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib.resources import files
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import tomllib

from jsonschema import Draft202012Validator, ValidationError

from ..runtime.artifacts import canonical_hash, safe_path

_ENV_KEYS = frozenset({'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP',
                       'USERPROFILE', 'HOME', 'APPDATA', 'LOCALAPPDATA', 'CODEX_HOME',
                       'COMSPEC', 'SYSTEMDRIVE', 'PROGRAMFILES', 'PROGRAMFILES(X86)'})


class CodexReviewer:
    """A reviewer whose execution provenance is produced by this adapter, never the model."""

    def __init__(self, *, model=None, executable='codex', timeout=180,
                 max_output_bytes=1024 * 1024, max_input_bytes=65536):
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError('Codex timeout은 유한한 양수여야 합니다')
        if (type(max_output_bytes) is not int or max_output_bytes < 1024
                or type(max_input_bytes) is not int or max_input_bytes < 1024):
            raise ValueError('Codex 입출력 한도는 1024바이트 이상의 정수여야 합니다')
        self.model_origin = 'explicit'
        if model is None:
            self.model_origin = 'config'
            config_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
            try:
                model = tomllib.loads((config_home / 'config.toml').read_text(encoding='utf-8')).get('model')
            except (OSError, ValueError):
                raise ValueError('Codex 리뷰 모델을 명시하거나 로컬 설정의 model을 확인하세요') from None
        if (not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,119}', model)
                or not isinstance(executable, (str, os.PathLike)) or not str(executable)):
            raise ValueError('Codex 실행 파일과 명시적인 리뷰 모델이 필요합니다')
        self.model = model
        self.executable = str(executable)
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self.max_input_bytes = max_input_bytes
        self.last_execution = None

    def _execute(self, command, cwd, prompt):
        env = {key: value for key, value in os.environ.items() if key.upper() in _ENV_KEYS}
        env.update(PYTHONIOENCODING='utf-8', NO_COLOR='1')
        try:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, cwd=cwd, env=env, shell=False,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except (OSError, ValueError):
            raise RuntimeError('codex review: executable_unavailable') from None
        overflow = threading.Event()
        buffers = [bytearray(), bytearray()]
        def drain(stream, target):
            try:
                while True:
                    chunk = stream.read(4096)
                    if not chunk:
                        break
                    room = self.max_output_bytes + 1 - len(target)
                    if room > 0:
                        target.extend(chunk[:room])
                    if len(target) > self.max_output_bytes:
                        overflow.set()
                        process.kill()
                        break
            except (OSError, ValueError):
                pass
            finally:
                stream.close()
        def feed():
            try:
                process.stdin.write(prompt)
                process.stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                pass
        threads = [threading.Thread(target=drain, args=(process.stdout, buffers[0]), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, buffers[1]), daemon=True),
                   threading.Thread(target=feed, daemon=True)]
        for thread in threads:
            thread.start()
        timed_out = False
        try:
            code = process.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            code = None
        finally:
            for thread in threads:
                thread.join(timeout=2)
        if timed_out:
            raise RuntimeError('codex review: timeout')
        if overflow.is_set() or any(thread.is_alive() for thread in threads):
            raise RuntimeError('codex review: output_limit')
        if code != 0:
            raise RuntimeError('codex review: execution_failed')
        return bytes(buffers[0]), bytes(buffers[1])

    def _parse(self, raw):
        thread_id, observed_model, observed_provider, final_text, completed = None, None, None, None, False
        try:
            for line in raw.decode('utf-8').splitlines():
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError()
                event_type = event.get('type')
                if event_type in {'error', 'turn.failed'}:
                    raise ValueError()
                if event_type == 'thread.started':
                    thread_id = event.get('thread_id')
                    observed_model = event.get('model', observed_model)
                    observed_provider = event.get('model_provider', observed_provider)
                if event_type in {'session_meta', 'turn_context', 'session.configured'}:
                    payload = event.get('payload', event)
                    if isinstance(payload, dict):
                        observed_model = payload.get('model', observed_model)
                        observed_provider = payload.get('model_provider', payload.get('provider', observed_provider))
                if event_type == 'item.completed' and isinstance(event.get('item'), dict):
                    item = event['item']
                    if item.get('type') == 'agent_message':
                        final_text = item.get('text')
                if event_type == 'turn.completed':
                    completed = True
            if (not completed or not isinstance(thread_id, str) or not thread_id
                    or not isinstance(final_text, str)):
                raise ValueError()
            decision = json.loads(final_text)
            schema = json.loads(files('savetax').joinpath('schemas/review-decision-v1.json').read_text(encoding='utf-8'))
            Draft202012Validator(schema).validate(decision)
            if observed_provider not in (None, 'openai') or observed_model not in (None, self.model):
                raise ValueError()
        except (UnicodeError, ValueError, TypeError, ValidationError):
            raise RuntimeError('codex review: invalid_output_or_metadata') from None
        return decision, thread_id, observed_model, observed_provider

    def review(self, package_dir, manifest):
        """Review a copied staging directory and return only the schema-checked decision."""
        self.last_execution = None
        original = Path(package_dir).absolute()
        try:
            safe_path(original, 'manifest.json')
            package = original.resolve(strict=True)
            total_size = 0
            for path in package.rglob('*'):
                if path.is_symlink():
                    raise ValueError()
                if path.is_file():
                    total_size += path.stat().st_size
                if total_size > 80 * 1024 * 1024:
                    raise ValueError()
        except (OSError, ValueError):
            raise RuntimeError('codex review: invalid_staging_input') from None
        prompt = files('savetax').joinpath('prompts/codex-review-v1.txt').read_text(encoding='utf-8')
        prompt += '\nBroker package hash: ' + str(manifest.get('package_hash', '')) + '\n'
        encoded = prompt.encode('utf-8')
        if len(encoded) > self.max_input_bytes:
            raise RuntimeError('codex review: input_limit')
        started = datetime.now(timezone.utc).isoformat()
        # A repository descendant can inherit AGENTS.md and unrelated research
        # instructions. System-temp staging has only the explicitly copied package.
        with tempfile.TemporaryDirectory(prefix='savetax-codex-review-') as temporary:
            staging = Path(temporary)
            evidence = staging / 'evidence'
            shutil.copytree(package, evidence)
            schema = staging / 'review-decision-v1.json'
            schema.write_bytes(files('savetax').joinpath('schemas/review-decision-v1.json').read_bytes())
            command = [self.executable, 'exec', '--json', '--sandbox', 'read-only',
                       '--ephemeral', '--ignore-user-config', '--skip-git-repo-check',
                       '--output-schema', str(schema), '--model', self.model,
                       '-c', 'model_provider="openai"', '--color', 'never', '-']
            stdout, stderr = self._execute(command, evidence, encoded)
        decision, thread_id, observed_model, observed_provider = self._parse(stdout)
        self.last_execution = {'kind': 'codex-exec', 'provider': 'openai',
                               'model': observed_model or self.model,
                               'requested_model': self.model, 'model_origin': self.model_origin,
                               'model_observed': observed_model, 'provider_observed': observed_provider,
                               'metadata_source': 'jsonl' if observed_model else 'configured-execution',
                               'metadata_limitation': None if observed_model else 'CLI JSONL did not report the resolved model; argv fixes the requested model and cloud provider.',
                               'thread_id': thread_id, 'returncode': 0,
                               'command': command, 'started_at': started,
                               'observed_at': datetime.now(timezone.utc).isoformat(),
                               'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
                               'stderr_sha256': hashlib.sha256(stderr).hexdigest(),
                               'decision_sha256': canonical_hash(decision),
                               'package_sha256': manifest['package_hash']}
        return decision
