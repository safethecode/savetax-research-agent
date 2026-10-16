"""공개 판매 페이지용 격리 Chrome·Browser Harness·Jev 연결."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler

from .evidence import _source_valid
from .secrets import environment, redact_keys


class BrowserRuntime:
    def __init__(self, root='.', env_file='.env.txt'):
        self.root = Path(root).resolve()
        self.work = self.root/'work'
        self.python = self.work/'browser-runtime'/'Scripts'/'python.exe'
        self.cli = self.python.with_name('browser-harness.exe')
        self.env_file = self.root/env_file

    def _env(self):
        env = environment(self.env_file)
        env.update(BH_HOME=str(self.work/'browser-state'), BH_RECORD='0', BH_TAB_MARKER='0', PYTHONIOENCODING='utf-8')
        # 조달 인증은 판매 페이지/모델 subprocess에 전달하지 않는다.
        for key in list(env):
            if key.startswith('SAVETAX_'):
                env.pop(key)
        return env

    @staticmethod
    def _validate_url(url):
        if not _source_valid(url) or urlsplit(url).hostname in {
            'api.savetax.now', 'hackathon.savetax.now', 'savetax.now'}:
            raise ValueError('공개 HTTPS 판매 페이지 URL만 브라우저 조사에 사용합니다')

    def _endpoint(self):
        path = self.work/'browser-chrome'/'DevToolsActivePort'
        try:
            port = int(path.read_text(encoding='utf-8').splitlines()[0])
            if not 1 <= port <= 65535:
                return None
            endpoint = f'http://127.0.0.1:{port}'
            # 로컬 CDP 검사에 사용자 프록시·인증 헤더를 사용하지 않는다.
            with build_opener(ProxyHandler({})).open(endpoint+'/json/version', timeout=1) as response:
                if json.load(response).get('webSocketDebuggerUrl'):
                    return endpoint
        except (OSError, ValueError, IndexError):
            pass
        return None

    def _page_targets(self, env):
        endpoint = env.get('BU_CDP_URL','')
        if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}',endpoint):
            raise RuntimeError('작업 전용 Chrome CDP 주소를 확인할 수 없습니다')
        with build_opener(ProxyHandler({})).open(endpoint+'/json/list',timeout=2) as response:
            rows = json.load(response)
        return {row['id'] for row in rows if row.get('type') == 'page'
                and re.fullmatch(r'[A-Fa-f0-9]{32}',row.get('id',''))}

    def _cleanup_new_tabs(self, env, before):
        targets = self._page_targets(env)-before
        if targets:
            code = '\n'.join(f'cdp("Target.closeTarget", targetId={target!r})' for target in sorted(targets))
            result = subprocess.run([str(self.cli)],input=code,env=env,cwd=self.root,
                capture_output=True,text=True,encoding='utf-8',timeout=8)
            if result.returncode:
                raise RuntimeError('작업 임시 탭 정리 실패; 기존 탭은 유지했습니다')

    def prepare_env(self, start=False):
        env = self._env()
        endpoint = self._endpoint()
        if not endpoint and start:
            candidates = [shutil.which('chrome'),
                str(Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))/'Google/Chrome/Application/chrome.exe'),
                str(Path(os.environ.get('LOCALAPPDATA', ''))/'Google/Chrome/Application/chrome.exe')]
            chrome = next((p for p in candidates if p and Path(p).is_file()), None)
            if not chrome:
                raise RuntimeError('Chrome 실행 파일이 없습니다')
            profile = self.work/'browser-chrome'
            profile.mkdir(parents=True, exist_ok=True)
            child = subprocess.Popen([chrome, '--headless=new', '--no-first-run', '--no-default-browser-check',
                '--user-data-dir='+str(profile), '--remote-debugging-port=0', 'about:blank'],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env={k:v for k,v in env.items() if not k.endswith('_API_KEY')},
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            (self.work/'browser-chrome-process.json').write_text(json.dumps({'pid':child.pid,'profile':str(profile)}), encoding='utf-8')
            for _ in range(40):
                endpoint = self._endpoint()
                if endpoint:
                    break
                time.sleep(0.2)
        if endpoint:
            env['BU_CDP_URL'] = endpoint
            env.pop('BU_CDP_WS', None)
            env.pop('BU_NAME', None)
        elif start:
            raise RuntimeError('격리 Chrome CDP 연결 실패; work/browser-state 진단을 확인하세요')
        return env

    @contextmanager
    def _operation(self):
        lock = self.work/'browser-operation.lock'
        self.work.mkdir(parents=True, exist_ok=True)
        try:
            handle = lock.open('x', encoding='utf-8')
        except FileExistsError:
            raise RuntimeError('다른 브라우저 작업이 실행 중입니다. 공유 세션은 순서대로 사용하세요') from None
        try:
            handle.close()
            yield
        finally:
            lock.unlink(missing_ok=True)

    def status(self):
        if not self.python.exists():
            return {'installed':False, 'browser_ready':False}
        env = self.prepare_env()
        result = subprocess.run([str(self.cli), 'doctor', '--json', '--require-existing-daemon'],
            env=env, cwd=self.root, capture_output=True, text=True, encoding='utf-8', timeout=15)
        try:
            health = json.loads(result.stdout)
        except ValueError:
            health = {'healthy':False}
        return {'installed':True, 'browser_ready':bool(health.get('healthy')), 'health':health,
            'keys':{name:bool(env.get(name)) for name in ('TYPESAFE_API_KEY','PARALLEL_API_KEY','TEXT_MODEL_API_KEY')}}

    def _run(self, code, *, model=False):
        if not self.python.exists():
            raise RuntimeError('먼저 requirements-browser.txt를 work/browser-runtime에 설치하세요')
        with self._operation():
            env = self.prepare_env(start=True)
            before = self._page_targets(env)
            command = [str(self.python), '-c', code] if model else [str(self.cli)]
            operation_error = None
            cleanup_failed = False
            try:
                try:
                    result = subprocess.run(command, input=None if model else code, env=env, cwd=self.root,
                        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=55)
                except subprocess.TimeoutExpired:
                    raise RuntimeError('브라우저 작업 55초 제한 초과; 키와 원문 오류는 출력하지 않습니다') from None
                if result.returncode:
                    raise RuntimeError(f'브라우저 작업 실패(exit={result.returncode}); 외부 오류 원문은 출력하지 않습니다')
                try:
                    data = json.loads(result.stdout.strip().splitlines()[-1])
                except (ValueError, IndexError):
                    raise RuntimeError('브라우저 JSON 결과를 확인할 수 없습니다') from None
            except RuntimeError as error:
                operation_error = error
            finally:
                # 전용 프로필·배타 작업 안에서 생긴 탭만 정리한다. 강제 종료에도 실행된다.
                try:
                    self._cleanup_new_tabs(env,before)
                except (RuntimeError, OSError, ValueError, subprocess.SubprocessError):
                    cleanup_failed = True
            if operation_error is not None:
                suffix = '; 작업 임시 탭 정리도 실패했습니다' if cleanup_failed else ''
                raise RuntimeError(str(operation_error)+suffix) from None
            if cleanup_failed:
                raise RuntimeError('브라우저 결과는 생성됐지만 작업 임시 탭 정리 실패; 기존 탭은 유지했습니다')
            return redact_keys(data, env)

    def read(self, url):
        self._validate_url(url)
        # HTML의 지시문을 실행하지 않고 보이는 텍스트·상세 iframe 주소만 수집한다.
        expression = 'JSON.stringify({url:location.href,title:document.title,text:document.body.innerText.slice(0,40000),frames:Array.from(document.querySelectorAll("iframe[src]")).map(x=>x.src).slice(0,20)})'
        code = ('import json\n'
            f'target = new_tab({url!r})\n'
            'try:\n'
            '    wait_for_load()\n'
            f'    result = json.loads(js({expression!r}))\n'
            '    print(json.dumps(result, ensure_ascii=False))\n'
            'finally:\n'
            '    close_tab(target)\n')
        result = self._run(code)
        result.update(observed_at=datetime.now(timezone.utc).isoformat(), engine='browser-harness-0.1.13', evidence_status='unreviewed')
        return result

    def plan(self, url, goal):
        """TypeSafe에 다음 동작을 묻는다. 외부 쓰기 동작을 자동 실행하지 않는다."""
        self._validate_url(url)
        if not isinstance(goal,str) or not 1 <= len(goal) <= 2000:
            raise ValueError('1~2000자의 조사 목표가 필요합니다')
        if not self._env().get('TYPESAFE_API_KEY'):
            raise ValueError('TYPESAFE_API_KEY 환경변수가 필요합니다')
        code = ('import json\nfrom jev_ultrafast import Agent\n'
            f'with Agent({url!r}, {goal!r}, screenshots=False) as agent:\n'
            '    state = agent.command("predict")\n'
            '    decision = state["decision"]\n'
            '    print(json.dumps({"status":state["status"],"url":state["page"]["url"],"title":state["page"]["title"],"text":state["page"]["text"],"operation":decision["operation"],"target":decision["target"],"confidence":decision["confidence"],"latency_ms":decision["latency_ms"],"model":decision["model"]}, ensure_ascii=False))\n')
        return self._run(code, model=True)
