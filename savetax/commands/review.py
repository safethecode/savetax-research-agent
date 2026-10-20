"""Codex reviews a fixed evidence package, with no publication side effect."""
import json
from ..adapters.codex import CodexReviewer
from ..application.review import review_package


def add_parser(sub):
    parser=sub.add_parser('review',help='고정 근거·본문을 Codex로 리뷰 (접수 없음)')
    parser.add_argument('--package',required=True)
    parser.add_argument('--model',default='gpt-6.1-sol',help='명시적 Codex 클라우드 리뷰 모델')


def execute(args):
    path=review_package(args.package,CodexReviewer(model=args.model))
    print(json.dumps({'review_path':str(path)},ensure_ascii=False))
    return 0
