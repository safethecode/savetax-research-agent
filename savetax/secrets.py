"""사용자가 제공한 키를 메모리에서만 환경변수로 읽는다."""
import os
import re
from pathlib import Path

ALLOWED_KEYS = frozenset({
    'TYPESAFE_API_KEY', 'PARALLEL_API_KEY', 'TEXT_MODEL_API_KEY',
    'TEXT_MODEL_BASE_URL', 'TEXT_MODEL', 'TEXT_MODEL_REASONING', 'TYPESAFE_MODEL',
})


def load_env_file(path='.env.txt'):
    """셸 평가 없이 허용된 NAME=value만 파싱한다. 값은 출력하지 않는다."""
    values = {}
    source = Path(path)
    if not source.exists():
        return values
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.*)', line)
        if not match or match[1] not in ALLOWED_KEYS:
            continue
        key, value = match.groups()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif ' #' in value:
            value = value.split(' #', 1)[0].rstrip()
        if value and '\x00' not in value:
            values[key] = value
    return values


def environment(path='.env.txt'):
    """기존 환경변수를 우선하며, 파일은 빈 환경변수만 채운다."""
    result = os.environ.copy()
    for key, value in load_env_file(path).items():
        if not result.get(key):
            result[key] = value
    return result


def redact_keys(value, env):
    """외부 응답·로컬 산출물에서 이 프로세스가 받은 키를 제거한다."""
    secrets = [v for k, v in env.items() if k.endswith('_API_KEY') and v]
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, '[REDACTED]')
        return value
    if isinstance(value, dict):
        return {redact_keys(k, env): redact_keys(v, env) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_keys(v, env) for v in value]
    return value
