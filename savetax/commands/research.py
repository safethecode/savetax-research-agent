"""Explicit invocation; never schedules work or sends competition submissions."""
import json
from pathlib import Path

from ..adapters.ollama import OllamaClient
from ..application.research import ResearchTools, run_research, validate_policy, rate_limit_metadata, cooldown_active
from ..runtime.artifacts import atomic_json
from ..runtime.config import LocalProfile


def add_parser(sub):
    parser=sub.add_parser('research',help='로컬 Qwen 제한 조사·근거 묶음 생성 (접수 없음)')
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input',help='공식 item/event와 선택적 원문 sources JSON')
    source.add_argument('--item-id',nargs='+',help='공식 API에서 읽을 물품 번호')
    parser.add_argument('--policy',required=True,help='현재 실행의 명시적 정책 JSON')
    parser.add_argument('--run-dir',required=True)
    parser.add_argument('--profile',help='비밀 없는 LocalProfile JSON; 기본 qwen3.5:9b')
    parser.add_argument('--tools',action='store_true',help='Parallel 검색과 Jev 읽기 허용 (API 비용 발생)')
    parser.add_argument('--root',default='.',help='기존 브라우저 런타임과 환경 파일의 저장소 root')
    parser.add_argument('--env-file',default='.env.txt')
    parser.add_argument('--guide',default=None)


def execute(args):
    policy=validate_policy(json.loads(Path(args.policy).read_text(encoding='utf-8-sig')))
    profile=LocalProfile(**json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))) if args.profile else LocalProfile()
    model=OllamaClient(profile)
    tools=ResearchTools(args.root,args.env_file) if args.tools else None
    failed=False
    if args.input:
        path=Path(args.input).resolve()
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        inputs=data.get('jobs',[data])
        for job in inputs:
            for source in job.get('sources',[]):
                source['path']=str((path.parent/source['path']).resolve())
    else:
        from ..adapters.catalog import SaveTaxClient, SaveTaxError
        import re
        if any(not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',value) for value in args.item_id):
            raise ValueError('invalid item_id')
        if len(args.item_id)>policy['max_candidates']:
            raise ValueError('candidate budget exceeded; split input explicitly')
        fetch_path=Path(args.run_dir)/'fetch-state.json'
        fetch_state=json.loads(fetch_path.read_text(encoding='utf-8')) if fetch_path.exists() else {'failures':[]}
        if cooldown_active(fetch_state.get('retry_not_before')):
            raise RuntimeError('official API Retry-After cooldown has not elapsed')
        client=SaveTaxClient(guide_path=args.guide)
        base='https://hackathon.savetax.now/v1/events/current'
        def record_failure(item_id,error):
            fetch_state['failures'].append({'item_id':item_id,'error_type':type(error).__name__,
                'http_status':getattr(error,'status',None),'stage':getattr(error,'stage',None)})
            fetch_state.update(rate_limit_metadata(error))
            atomic_json(fetch_path,fetch_state)
            print(json.dumps({'item_id':item_id,'state':'official_fetch_failed',
                              'http_status':getattr(error,'status',None)},ensure_ascii=False))
        try:
            event=client.get_json(base)
        except SaveTaxError as error:
            record_failure(None,error)
            return 2
        def live_jobs():
            nonlocal failed
            for item_id in args.item_id:
                try:
                    lookup=client.get_json(base+'/items/lookup',params={'ids':item_id})
                    matching=[row for row in lookup.get('items',[]) if row.get('item_id')==item_id]
                    if len(matching)!=1 or matching[0].get('state')!='available':
                        print(item_id+': 현재 available 아님; 조사 건너뜀')
                        continue
                    item=client.get_json(base+'/items/'+item_id)
                    item['availability']=matching[0]
                except SaveTaxError as error:
                    failed=True
                    record_failure(item_id,error)
                    if error.status==429:
                        break
                    continue
                yield {'item':item,'event':event,'sources':[]}
        inputs=live_jobs()
    if isinstance(inputs,list) and len(inputs)>policy['max_candidates']:
        raise ValueError('candidate budget exceeded; split input explicitly')
    for job in inputs:
        try:
            state=run_research(job,policy,args.run_dir,model=model,tools=tools)
            print(json.dumps({'item_id':state['item_id'],'state':state['state'],
                              'package_dir':state.get('package_dir')},ensure_ascii=False))
        except (ValueError,RuntimeError,OSError) as error:
            failed=True
            # Provider error bodies and source text never appear in this summary.
            print(json.dumps({'item_id':job.get('item',{}).get('item_id'),'state':'failed_or_retry_wait',
                              'error_type':type(error).__name__},ensure_ascii=False))
    return 2 if failed else 0
