"""Bounded local research. Tool results and model suggestions never authorize writes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
from importlib.resources import files
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator, ValidationError

from ..domain.scoring import build_draft, calculate_body
from ..runtime.artifacts import canonical_hash, atomic_json, safe_path, exclusive_lock


def _resource(name):
    return files('savetax').joinpath(name).read_text(encoding='utf-8')


def validate_policy(policy):
    if not isinstance(policy,dict) or policy.get('schema_version') != '1':
        raise ValueError('policy schema_version must be 1')
    if not isinstance(policy.get('policy_id'),str) or not policy['policy_id'].strip():
        raise ValueError('explicit policy_id required')
    for key in ('allow_submit','allow_revise'):
        if type(policy.get(key)) is not bool:
            raise ValueError('explicit publication scope required: '+key)
    for key, maximum in (('max_actions',30),('max_searches',10),('max_reads',10),
                         ('max_attempts',5),('max_candidates',20),('jev_steps',8)):
        if type(policy.get(key)) is not int or not 1 <= policy[key] <= maximum:
            raise ValueError('invalid policy budget: '+key)
    return policy


def rate_limit_metadata(error):
    if getattr(error,'status',None)!=429:
        return {}
    seconds=getattr(error,'retry_after',None)
    seconds=seconds if type(seconds) is int and seconds>=0 else 60
    return {'http_status':429,'retry_after':seconds,
            'retry_not_before':(datetime.now(timezone.utc)+timedelta(seconds=seconds)).isoformat()}


def cooldown_active(value):
    if not value:
        return False
    try:
        deadline=datetime.fromisoformat(value)
        return deadline>datetime.now(timezone.utc)
    except (ValueError,TypeError):
        raise ValueError('invalid persisted provider cooldown') from None


class ResearchTools:
    """Fixed read-only broker: Parallel discovery and existing guarded Jev loop."""

    def __init__(self, root, env_file='.env.txt', session='local-research'):
        self.root, self.env_file, self.session = Path(root), env_file, session

    def search(self, query):
        from ..adapters.parallel import ParallelClient
        from ..runtime.secrets import load_env_file
        import os
        key = os.environ.get('PARALLEL_API_KEY') or load_env_file(self.root/self.env_file).get('PARALLEL_API_KEY')
        return ParallelClient(api_key=key).search(query, max_results=5)

    def read(self, url, steps):
        from ..adapters.browser import BrowserRuntime
        goal = ('공개 상품 상세에서 실제 모델, 선택 옵션, 신품 일반 판매가, 한 팩 수량, '
                '부가세, 배송비, 완제품 구성과 구매 가능 표시를 읽는다. '
                '구매·장바구니·로그인·문의·판매자 연락·차단 우회는 하지 않는다.')
        return BrowserRuntime(root=self.root,env_file=self.env_file,session_name=self.session).run_jev(
            url,goal,max_steps=steps)


def _capture_sources(job_dir, data):
    captured, ids = [], set()
    for source in data.get('sources',[]):
        sid = source.get('source_id')
        if not isinstance(sid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',sid) or sid in ids:
            raise ValueError('invalid or duplicate source_id')
        ids.add(sid)
        path = Path(source['path'])
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 4_000_000:
            raise ValueError('source must be a regular file at most 4MB')
        raw = path.read_bytes()
        raw.decode('utf-8')
        target = safe_path(job_dir,'sources/'+sid+'.txt')
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=raw:
            raise ValueError('captured source changed; start a new run')
        target.write_bytes(raw)
        captured.append({**source,'path':str(target.resolve()),'bytes':len(raw)})
    return captured


def _source_hashes(sources):
    result={}
    for source in sources:
        path=Path(source['path'])
        if not path.is_file() or path.is_symlink() or path.stat().st_size>4_000_000:
            raise ValueError('source must be a regular file at most 4MB')
        with path.open('rb') as stream:
            raw=stream.read(4_000_001)
        if len(raw)>4_000_000:
            raise ValueError('source exceeds size budget')
        result[source['source_id']]=hashlib.sha256(raw).hexdigest()
    return result


def _draft(data, proposal, sources):
    """Adopt only source-backed observed proposals into an unapproved draft.

    Initial automated draft supports identical complete single-unit products.
    Alternative/unit-conversion hypotheses are retained for further evidence.
    """
    blocking = list(proposal['unknowns'])
    by_source = {s['source_id']:s for s in sources}
    claims, values = {}, {}
    for claim in proposal['claims']:
        field = claim['field']
        if field in claims:
            blocking.append('duplicate field: '+field)
        claims[field] = claim
        source = by_source.get(claim['source_id'])
        quote = claim['quote']
        if (claim['status']!='observed' or source is None or source.get('kind') not in ('retailer','manufacturer')
                or not quote or quote not in Path(source['path']).read_text(encoding='utf-8')):
            blocking.append('unresolved source/observation: '+field)
        else:
            values[field]=claim['value']
    required = ('model','unit_price','vat_included','shipping_included','pack_quantity','unit',
                'new','purchase_available','complete_product')
    for field in required:
        if field not in values:
            blocking.append('missing observed field: '+field)
    for field in ('model','unit'):
        if not isinstance(values.get(field),str) or not values[field].strip():
            blocking.append('invalid text field: '+field)
    if (not isinstance(values.get('unit_price'),str)
            or not re.fullmatch(r'[0-9]{1,30}',values['unit_price'])
            or Decimal(values['unit_price'])<=0):
        blocking.append('invalid integer KRW price')
    if type(values.get('pack_quantity')) is not int or not 1<=values['pack_quantity']<=1000000:
        blocking.append('invalid pack quantity')
    if proposal['comparison_kind']!='identical':
        blocking.append('alternative comparison needs explicit specification and complete-cost evidence')
    for field in ('new','purchase_available','complete_product','shipping_included'):
        if values.get(field) is not True:
            blocking.append('missing complete new-product/cost evidence: '+field)
    if values.get('installation_required') is True:
        blocking.append('required installation costs need explicit comparison evidence')
    if blocking:
        return None,{'blocking':sorted(set(blocking)),'total_savings_krw':None}
    item = data['item']
    if (item.get('snapshot',{}).get('installation_required') is True
            or any(f.get('installation_required') is True for f in item.get('facts',[]))):
        return None,{'blocking':['official scope includes required installation; cost evidence needed'],
                     'total_savings_krw':None}
    if type(values['vat_included']) is not bool or type(values['pack_quantity']) is not int:
        return None,{'blocking':['invalid VAT or pack value'],'total_savings_krw':None}
    if any(f.get('scorable') and f.get('unit')!=values['unit'] for f in item['facts']):
        return None,{'blocking':['official unit conversion not established'],'total_savings_krw':None}
    source = by_source[claims['unit_price']['source_id']]
    if source.get('kind')!='retailer':
        return None,{'blocking':['price requires actual retailer observation'],'total_savings_krw':None}
    offer = {key:values[key] for key in ('model','unit_price','vat_included','shipping_included','pack_quantity')}
    offer.update(url=source['url'],quote=claims['unit_price']['quote'],observed_at=source.get('observed_at'))
    # Required pack ends are purchased separately for each official fact.
    pack = values['pack_quantity']
    if pack > 1:
        prices = {}
        for fact in item['facts']:
            if fact.get('scorable'):
                q = Decimal(fact['quantity'])
                packs = (q/pack).to_integral_value(rounding=ROUND_CEILING)
                prices[fact['fact_id']] = format((packs*Decimal(str(values['unit_price']))/q).quantize(
                    Decimal('0.000001'),rounding=ROUND_CEILING),'f')
        offer['benchmark_unit_price_by_fact']=prices
    try:
        body = build_draft(item,offer,data['event'])
        return body,calculate_body(item,body)
    except (ValueError,ArithmeticError,KeyError) as error:
        return None,{'blocking':['draft validation: '+str(error)],'total_savings_krw':None}


def run_research(data, policy, run_dir, *, model, tools=None):
    """One candidate per resumable job; all budgets survive restarts."""
    from .review import create_package
    validate_policy(policy)
    item = data['item']
    item_id = item.get('item_id')
    if not isinstance(item_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',item_id):
        raise ValueError('invalid item_id')
    if item.get('availability',{}).get('state')!='available':
        raise ValueError('research requires available official item')
    run_dir=safe_path(Path(run_dir).absolute(),'run.json').parent
    run_dir.mkdir(parents=True,exist_ok=True)
    schema=json.loads(_resource('schemas/research-action-v1.json'))
    with exclusive_lock(run_dir/'.run.lock'):
        source_hashes=_source_hashes(data.get('sources',[]))
        identity={'input_hash':canonical_hash({'data':data,'source_hashes':source_hashes}),
                  'policy_hash':canonical_hash(policy)}
        run_path=safe_path(run_dir,'run.json')
        profile = getattr(getattr(model,'profile',None),'as_dict',lambda:{'model':'explicit-test-adapter'})()
        if run_path.exists():
            saved=json.loads(run_path.read_text(encoding='utf-8'))
            if saved.get('policy_hash')!=identity['policy_hash'] or saved.get('profile')!=profile:
                raise ValueError('run policy or model profile changed; start a new run')
            if cooldown_active(saved.get('retry_not_before')):
                raise RuntimeError('provider Retry-After cooldown has not elapsed')
        else:
            atomic_json(run_path,{'schema_version':'1','policy_hash':identity['policy_hash'],'profile':profile})
            atomic_json(run_dir/'effective-policy.json',policy)
        jobs=[p for p in (run_dir/'jobs').glob('*/job.json')] if (run_dir/'jobs').exists() else []
        if len(jobs)>=policy['max_candidates'] and not (run_dir/'jobs'/item_id/'job.json').exists():
            raise ValueError('run candidate budget exhausted')
        job_dir=safe_path(run_dir,'jobs/'+item_id)
        job_dir.mkdir(parents=True,exist_ok=True)
        path=job_dir/'job.json'
        state=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
            'schema_version':'1','item_id':item_id,**identity,'state':'queued','attempts':0,
            'actions':0,'searches':0,'reads':0,'sources':[],'discovered_urls':[],'history':[]}
        if any(state.get(k)!=v for k,v in identity.items()):
            raise ValueError('job inputs or policy changed; start a new run')
        if state['state'] in ('awaiting_review','approved','needs_evidence','rejected'):
            return state
        if state['state']=='failed' or state['attempts']>=policy['max_attempts']:
            raise ValueError('job attempts exhausted; preserve evidence and start explicit new job')
        if state['state']=='queued':
            state['sources']=_capture_sources(job_dir,data)
            atomic_json(job_dir/'official'/'snapshot.json',{'item':item,'event':data['event']})
        state.update(state='running',attempts=state['attempts']+1)
        atomic_json(path,state)
        try:
            while state['actions'] < policy['max_actions']:
                state['actions']+=1
                atomic_json(path,state)  # account even an interrupted/timeout call
                remaining=10000
                snippets=[]
                for source in state['sources']:
                    text=Path(source['path']).read_text(encoding='utf-8')
                    take=min(len(text),6000,remaining)
                    snippets.append({key:source.get(key) for key in ('source_id','url','kind','observed_at','truncated')}
                                    | {'text':text[:take],'context_truncated':take<len(text)})
                    remaining-=take
                context={'model':item.get('snapshot',{}).get('model'),'item_id':item_id,
                         'official_snapshot_excerpt':json.dumps(item.get('snapshot',{}),ensure_ascii=False)[:2000],
                         'official_snapshot_context_truncated':len(json.dumps(item.get('snapshot',{}),ensure_ascii=False))>2000,
                         'units':sorted({f.get('unit','') for f in item.get('facts',[]) if f.get('scorable')}),
                         'sources':snippets,'discovered_urls':state['discovered_urls'],
                         'recent_search':[{'query':h['query'],'results':[
                             {k:str(r.get(k,''))[:1200] for k in ('source_url','title','excerpt')}
                             for r in h['results'][:2]]} for h in state['history'][-2:]],
                         'remaining_actions':policy['max_actions']-state['actions']}
                action=model.generate(_resource('prompts/research-v1.txt')+'\nDATA:\n'+json.dumps(context,ensure_ascii=False),schema)
                try:
                    Draft202012Validator(schema).validate(action)
                except ValidationError:
                    raise ValueError('model action/proposal violates schema') from None
                atomic_json(job_dir/'proposals'/f"action-{state['actions']:03}.json",{
                    'action':action,'model_metadata':getattr(model,'last_metadata',{}),
                    'context_hash':canonical_hash(context),'schema_hash':canonical_hash(schema)})
                if action['action']=='finish':
                    if action['proposal'] is None:
                        raise ValueError('finish requires a proposal')
                    proposal=action['proposal']
                    body,calculation=_draft(data,proposal,state['sources'])
                    atomic_json(job_dir/'calculations'/'draft.json',calculation)
                    package=create_package(job_dir/'packages',item=item,event=data['event'],policy=policy,
                        proposal=proposal,sources=state['sources'],calculation=calculation,body=body)
                    state.update(state='awaiting_review',package_dir=str(package.resolve()))
                    atomic_json(path,state)
                    return state
                if tools is None:
                    raise ValueError('live tools disabled for snapshot-only run')
                if action['action']=='search':
                    if state['searches']>=policy['max_searches'] or not action['query']:
                        raise ValueError('search budget exhausted or missing query')
                    state['searches']+=1
                    atomic_json(path,state)
                    result=tools.search(action['query'])
                    atomic_json(job_dir/'search'/f"search-{state['searches']:03}.json",result)
                    for row in result.get('results',[]):
                        url=row.get('source_url')
                        if (isinstance(url,str) and len(url)<=2048 and len(state['discovered_urls'])<20
                                and url not in state['discovered_urls']):
                            state['discovered_urls'].append(url)
                    state['history'].append({'kind':'discovery_only','query':action['query'],'results':result.get('results',[])})
                elif action['action']=='read':
                    if state['reads']>=policy['max_reads'] or action['url'] not in state['discovered_urls']:
                        raise ValueError('read budget exhausted or URL was not discovered')
                    state['reads']+=1
                    atomic_json(path,state)
                    result=tools.read(action['url'],policy['jev_steps'])
                    sid='read-'+str(state['reads'])
                    while sid in {s['source_id'] for s in state['sources']}:
                        sid+='-capture'
                    raw_path=job_dir/'sources'/(sid+'.json')
                    atomic_json(raw_path,result)
                    text=result.get('text')
                    if not isinstance(text,str):
                        raise ValueError('browser observation missing text')
                    target=job_dir/'sources'/(sid+'.txt')
                    target.write_text(text,encoding='utf-8')
                    state['sources'].append({'source_id':sid,'path':str(target),'url':result.get('url',action['url']),
                        'requested_url':action['url'],'kind':'retailer','method':'jev_ultrafast',
                        'observed_at':result.get('observed_at',datetime.now(timezone.utc).isoformat()),
                        'truncated':True,'capture_limit':40000,'raw_path':str(raw_path)})
                atomic_json(path,state)
            raise ValueError('action budget exhausted before finish; evidence preserved')
        except (ValueError,RuntimeError,OSError) as error:
            state.update(state='failed' if state['attempts']>=policy['max_attempts'] or state['actions']>=policy['max_actions'] else 'retry_wait',
                         error_type=type(error).__name__)
            cooldown=rate_limit_metadata(error)
            if cooldown:
                state.update(cooldown)
                run_state=json.loads(run_path.read_text(encoding='utf-8'))
                atomic_json(run_path,{**run_state,**cooldown})
            atomic_json(path,state)
            raise
