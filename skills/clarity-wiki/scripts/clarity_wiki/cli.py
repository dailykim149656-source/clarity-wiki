"""Standard-library command line interface; JSON results and stable exit codes."""

import argparse
import json

from . import __version__
from .workspace import InputError, Workspace


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError(message)


def main(argv=None) -> int:
    parser = Parser(prog='clarity-wiki', description='Local read-only revision and evidence checks.')
    parser.add_argument('--version', action='version', version=__version__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    audit = subparsers.add_parser('audit', help='Find numerical and quoted-text revision candidates.')
    audit.add_argument('--original', required=True)
    audit.add_argument('--revised', required=True)
    evidence = subparsers.add_parser('evidence', help='Inspect manifest structure and declared hashes; does not run tests.')
    evidence.add_argument('--manifest', required=True)
    for command in [audit, evidence]:
        command.add_argument('--root', required=True, help='Allowed workspace root; inputs are relative to this root.')
        command.add_argument('--limit', type=int, default=5, help='Maximum displayed findings (1–30).')
    try:
        args = parser.parse_args(argv)
        if not 1 <= args.limit <= 30:
            raise InputError('limit must be between 1 and 30')
        workspace = Workspace(args.root)
        if args.action == 'audit':
            from .audit import audit_revision
            result = audit_revision(workspace, args.original, args.revised, args.limit)
        else:
            from .evidence import check_evidence
            result = check_evidence(workspace, args.manifest, args.limit)
        exit_code = 1 if result['total_findings'] else 0
    except InputError as error:
        result = {'status': 'error', 'error': str(error)[:500]}
        exit_code = 2
    output = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    print(output.encode('utf-8', errors='backslashreplace').decode('utf-8'))
    return exit_code
