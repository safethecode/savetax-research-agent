"""저장소 전용 Chrome에 연결해 Browser Harness MCP를 시작한다."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from savetax.browser import BrowserRuntime

if __name__ == '__main__':
    env = BrowserRuntime(ROOT).prepare_env(start=True)
    for key in list(env):
        if key.endswith('_API_KEY'):
            env.pop(key)
    os.environ.clear()
    os.environ.update(env)
    from browser_harness.mcp_cli import main
    main()
