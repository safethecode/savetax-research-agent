"""Explicit invocation; never schedules work or sends competition submissions."""
import json
from pathlib import Path

from ..adapters.ollama import OllamaClient
from ..application.research import ResearchTools, run_research, validate_policy
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
    if args.input:
        path=Path(args.input).resolve()
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        inputs=data.get('jobs',[data])
        for job in inputs:
            for source in job.get('sources',[]):
                source['path']=str((path.parent/source['path']).resolve())
    else:
        from ..client import SaveTaxClient
        import re
        if any(not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',value) for value in args.item_id):
            raise ValueError('invalid item_id')
        client=SaveTaxClient(guide_path=args.guide)
        base='https://hackathon.savetax.now/v1/events/current'
        event=client.get_json(base)
        inputs=[]
        for item_id in args.item_id[:policy['max_candidates']]:
            lookup=client.get_json(base+'/items/lookup',params={'ids':item_id})
            matching=[row for row in lookup.get('items',[]) if row.get('item_id')==item_id]
            if len(matching)!=1 or matching[0].get('state')!='available':
                print(item_id+': 현재 available 아님; 조사 건너뜀')
                continue
            item=client.get_json(base+'/items/'+item_id)
            item['availability']=matching[0]
            inputs.append({'item':item,'event':event,'sources':[]})
    if len(inputs)>policy['max_candidates']:
        raise ValueError('candidate budget exceeded; split input explicitly')
    failed=False
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
