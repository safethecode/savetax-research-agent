"""Score CLI arguments; publication and recovery live in application."""
from ..application.publication import run_score


def add_parser(sub):
    parser=sub.add_parser('score',help='리뷰한 신규 후보를 preview 후 접수 (--send)')
    parser.add_argument('--input',required=True)
    parser.add_argument('--receipt',required=True)
    parser.add_argument('--guide',default=None)
    parser.add_argument('--min-saving',default='0')
    parser.add_argument('--package',help='Codex가 검토한 고정 근거 묶음 (--send 필수)')
    parser.add_argument('--review',help='근거 묶음과 일치하는 broker 리뷰 (--send 필수)')
    parser.add_argument('--send',action='store_true')


def execute(args):
    return run_score(args)
