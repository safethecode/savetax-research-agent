"""공개 판매 페이지용 격리 Chrome·Browser Harness·Jev 연결."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
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

# Jev 실행 루프가 누르지 않을 대상: 구매·장바구니·결제·주문·로그인·가입·문의·업로드.
JEV_GUARD_PATTERN = r'구매|장바구니|결제|주문|로그인|회원가입|가입|문의|업로드|buy|cart|checkout|order|login|log in|sign ?in|sign ?up|register|upload'


class BrowserRuntime:
    def __init__(self, root='.', env_file='.env.txt', session_name=None):
        self.root = Path(root).resolve()
        self.work = self.root/'work'
        if session_name is not None and (
                not isinstance(session_name, str)
                or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,31}', session_name)
                or re.fullmatch(r'con|prn|aux|nul|com[1-9]|lpt[1-9]', session_name)):
            raise ValueError('세션 이름은 장치명을 제외한 1~32자의 영문 소문자·숫자·하이픈·밑줄만 허용합니다')
        self.session_name = session_name
        self.session_dir = self.work if session_name is None else self.work/'browser-sessions'/session_name
        self.profile = self.session_dir/'browser-chrome'
        self.state = self.session_dir/'browser-state'
        self.ipc_runtime = self.state/'runtime'
        if os.name != 'nt' and len(str(self.ipc_runtime/'bu.sock').encode()) >= 100:
            # macOS AF_UNIX paths have a 104-byte limit; keep durable data in work/.
            digest = hashlib.sha256(str(self.state).encode()).hexdigest()[:16]
            self.ipc_runtime = Path('/tmp')/f'savetax-bh-{os.getuid()}'/digest
        self.process_file = self.session_dir/'browser-chrome-process.json'
        self.python = self.work/'browser-runtime'/'Scripts'/'python.exe'
        self.cli = self.python.with_name('browser-harness.exe')
        if os.name != 'nt':
            self.python = self.work/'browser-runtime'/'bin'/'python'
            self.cli = self.python.with_name('browser-harness')
        self.env_file = self.root/env_file

    def _env(self):
        env = environment(self.env_file)
        env.update(BH_HOME=str(self.state), BH_RECORD='0', BH_TAB_MARKER='0', PYTHONIOENCODING='utf-8')
        if self.session_name is not None:
            env.update(BH_CONFIG_DIR=str(self.state), BH_RUNTIME_DIR=str(self.state/'runtime'),
                       BH_TMP_DIR=str(self.state/'tmp'), BH_AGENT_WORKSPACE=str(self.state/'agent-workspace'))
            # 이름 있는 세션은 상위 프로세스의 다른 Chrome 연결을 물려받지 않는다.
            for key in ('BU_CDP_URL', 'BU_CDP_WS', 'BU_NAME', 'BU_BROWSER_ID'):
                env.pop(key, None)
        if self.ipc_runtime != self.state/'runtime':
            env['BH_RUNTIME_DIR'] = str(self.ipc_runtime)
        # 조달 인증은 판매 페이지/모델 subprocess에 전달하지 않는다.
        for key in list(env):
            if key.startswith('SAVETAX_'):
                env.pop(key)
        return env

    @staticmethod
    def _validate_url(url):
        if not _source_valid(url):
            raise ValueError('공개 HTTPS 판매 페이지 URL만 브라우저 조사에 사용합니다')
        parsed = urlsplit(url)
        # 사용자 지정 후보 탐색 예외. 인증 API·계정 화면에는 확장하지 않는다.
        if parsed.hostname == 'savetax.now' and parsed.path == '/search':
            return
        if parsed.hostname in {'api.savetax.now', 'hackathon.savetax.now', 'savetax.now'}:
            raise ValueError('공개 HTTPS 판매 페이지 URL만 브라우저 조사에 사용합니다')

    def _endpoint(self):
        path = self.profile/'DevToolsActivePort'
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
                shutil.which('google-chrome'), shutil.which('chromium'),
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                str(Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))/'Google/Chrome/Application/chrome.exe'),
                str(Path(os.environ.get('LOCALAPPDATA', ''))/'Google/Chrome/Application/chrome.exe')]
            chrome = next((p for p in candidates if p and Path(p).is_file()), None)
            if not chrome:
                raise RuntimeError('Chrome 실행 파일이 없습니다')
            profile = self.profile
            profile.mkdir(parents=True, exist_ok=True)
            child = subprocess.Popen([chrome, '--headless=new', '--no-first-run', '--no-default-browser-check',
                '--user-data-dir='+str(profile), '--remote-debugging-port=0', 'about:blank'],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env={k:v for k,v in env.items() if not k.endswith('_API_KEY')},
                start_new_session=os.name != 'nt',
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.process_file.write_text(json.dumps({'pid':child.pid,'profile':str(profile)}), encoding='utf-8')
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
            raise RuntimeError('격리 Chrome CDP 연결 실패; '+str(self.state)+' 진단을 확인하세요')
        return env

    @contextmanager
    def _operation(self):
        lock = self.session_dir/'browser-operation.lock'
        self.session_dir.mkdir(parents=True, exist_ok=True)
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

    def _run(self, code, *, model=False, timeout=55):
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
                        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
                except subprocess.TimeoutExpired:
                    raise RuntimeError(f'브라우저 작업 {timeout}초 제한 초과; 키와 원문 오류는 출력하지 않습니다') from None
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

    def run_jev(self, url, goal, max_steps=8, fills=None):
        """Jev 실행 루프로 공개 판매 페이지를 직접 조작한다. 구매·로그인 계열 동작은 실행하지 않는다."""
        self._validate_url(url)
        if not isinstance(goal,str) or not 1 <= len(goal) <= 2000:
            raise ValueError('1~2000자의 조사 목표가 필요합니다')
        if type(max_steps) is not int or not 1 <= max_steps <= 20:
            raise ValueError('max_steps는 1~20이어야 합니다')
        fills = dict(fills or {})
        if any(not isinstance(k,str) or not isinstance(v,str) or not k.strip() or len(k)>100 or len(v)>100 for k,v in fills.items()):
            raise ValueError('입력값은 100자 이하의 라벨=값 쌍이어야 합니다')
        if not self._env().get('TYPESAFE_API_KEY'):
            raise ValueError('TYPESAFE_API_KEY 환경변수가 필요합니다')
        code = ('import json, re\nfrom jev_ultrafast import Agent\nfrom jev_ultrafast.model import field_context\n'
            f'FILLS = {fills!r}\n'
            f'GUARD = re.compile({JEV_GUARD_PATTERN!r}, re.I)\n'
            'steps = []\nstopped = None\n'
            f'with Agent({url!r}, {goal!r}, screenshots=False) as agent:\n'
            f'    for _ in range({max_steps}):\n'
            '        state = agent.command("predict")\n'
            '        d = state["decision"]\n'
            '        action = next((a for a in state["page"]["actions"] if a["id"] == d["choice"]), None)\n'
            '        label = (action or {}).get("label", d["choice"])\n'
            '        steps.append({"operation": d["operation"], "label": label[:200], "confidence": d["confidence"], "latency_ms": d["latency_ms"]})\n'
            '        if d["operation"] in ("DONE", "BLOCKED"):\n'
            '            agent.command("act", {"fingerprint": state["page"]["fingerprint"]})\n'
            '            stopped = d["operation"].lower(); break\n'
            '        if GUARD.search(label):\n'
            '            stopped = "guarded"; break\n'
            '        if d["operation"] == "TYPE_TEXT":\n'
            '            value = next((v for k, v in FILLS.items() if k in label), None)\n'
            '            if value is None:\n'
            '                stopped = "guarded"; break\n'
            '            agent.pending_text = (field_context(agent.state["goal"], action, state["page"], agent.state["history"]), value, None)\n'
            '            steps[-1]["text"] = value\n'
            '        agent.command("act", {"fingerprint": state["page"]["fingerprint"]})\n'
            '    page = agent.browser.observe(screenshot=False)\n'
            '    print(json.dumps({"stopped": stopped or "step_limit", "steps": steps, "url": page["url"], "title": page["title"], "text": page["text"][:40000], "model": (agent.state["decisions"] or [{}])[-1].get("model")}, ensure_ascii=False))\n')
        result = self._run(code, model=True, timeout=180)
        result.update(observed_at=datetime.now(timezone.utc).isoformat(), engine='jev_ultrafast', evidence_status='unreviewed')
        return result
