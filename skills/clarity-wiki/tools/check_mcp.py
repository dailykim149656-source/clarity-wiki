#!/usr/bin/env python3
"""Check both installed MCP tools over local stdio using temporary synthetic files."""

import argparse
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile


class CheckError(Exception):
    """A required MCP response was missing or unexpected."""


def tool_result(response):
    if response.isError or not isinstance(response.structuredContent, dict):
        raise CheckError('Tool returned an error or no structured result')
    result = response.structuredContent
    if type(result.get('total_findings')) is not int or result['total_findings'] < 0:
        raise CheckError('Tool returned an invalid total_findings')
    if not isinstance(result.get('findings'), list):
        raise CheckError('Tool returned no findings list')
    return result


async def check(root: Path, report: dict):
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as error:
        raise CheckError('MCP SDK missing; run this script with the installed Skill .venv/bin/python') from error

    launcher = Path(__file__).resolve().with_name('mcp_server.py')
    if not launcher.is_file():
        raise CheckError('Sibling mcp_server.py is missing; reinstall the Skill')
    with tempfile.TemporaryDirectory(prefix='.clarity-mcp-check-', dir=root) as directory:
        probe = Path(directory)
        (probe / 'before.txt').write_text('온도 -5°C\n', encoding='utf-8')
        (probe / 'after.txt').write_text('온도 5°C\n', encoding='utf-8')
        (probe / 'result.txt').write_text('synthetic health check only\n', encoding='utf-8')

        def relative(name):
            return (probe / name).relative_to(root).as_posix()

        def digest(name):
            return hashlib.sha256((probe / name).read_bytes()).hexdigest()

        manifest = {'version': 1, 'artifacts': [relative('result.txt')], 'requirements': [{
            'id': 'SYNTHETIC', 'criterion': 'Synthetic health check, not task evidence', 'status': 'verified',
            'evidence': [{'path': relative('result.txt'), 'sha256': digest('result.txt'),
                          'command': 'synthetic fixture; no command executed', 'exit_code': 0,
                          'inputs': [{'path': relative('before.txt'), 'sha256': digest('before.txt')}]}],
        }]}
        (probe / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        parameters = StdioServerParameters(command=sys.executable, args=[str(launcher), '--root', str(root)],
                                          cwd=str(root), env={'PYTHONDONTWRITEBYTECODE': '1'})
        report['stage'] = 'initialize'
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                report['checks'].append({'name': 'initialize', 'status': 'passed'})
                report['stage'] = 'tools/list'
                names = sorted(tool.name for tool in (await session.list_tools()).tools)
                if names != ['audit_revision', 'check_evidence']:
                    raise CheckError(f'Unexpected tool list: {names}')
                report['checks'].append({'name': 'tools/list', 'status': 'passed', 'tools': names})

                report['stage'] = 'audit_revision'
                audit = tool_result(await session.call_tool('audit_revision', {
                    'original': relative('before.txt'), 'revised': relative('after.txt'), 'limit': 5}))
                rules = sorted({item['rule'] for item in audit['findings']
                                if isinstance(item, dict) and isinstance(item.get('rule'), str)})
                if audit.get('status') != 'findings' or audit['total_findings'] < 1 or 'NUMBER_CHANGED' not in rules:
                    raise CheckError('audit_revision did not detect the synthetic sign change')
                report['checks'].append({'name': 'audit_revision', 'status': 'passed',
                                         'result_status': audit['status'], 'total_findings': audit['total_findings'],
                                         'rules': rules})

                report['stage'] = 'check_evidence'
                evidence = tool_result(await session.call_tool('check_evidence', {
                    'manifest': relative('manifest.json'), 'limit': 5}))
                if (evidence.get('status') != 'no_findings' or evidence['total_findings'] != 0
                        or evidence['findings']):
                    raise CheckError('check_evidence rejected the synthetic manifest or hashes')
                report['checks'].append({'name': 'check_evidence', 'status': 'passed',
                                         'result_status': evidence['status'], 'total_findings': 0})
                report['stage'] = 'shutdown'
        report['stage'] = 'cleanup'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Installed project folder; defaults to cwd')
    parser.add_argument('--timeout', type=float, default=30, help='Positive finite check timeout in seconds (default: 30)')
    args = parser.parse_args(argv)
    report = {'status': 'failed', 'scope': 'local_stdio', 'stage': 'setup', 'checks': []}
    try:
        if sys.version_info < (3, 10) or os.name != 'posix':
            raise CheckError('Python 3.10+ on POSIX macOS/Linux is required')
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise CheckError('--timeout must be positive and finite')
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise CheckError('Workspace must be an existing directory')
        report['workspace'] = str(root)
        asyncio.run(asyncio.wait_for(check(root, report), timeout=args.timeout))
        report.update(status='passed', stage='complete')
    except Exception as error:
        while len(getattr(error, 'exceptions', ())) == 1:
            error = error.exceptions[0]
        report['error'] = (f'MCP check timeout after {args.timeout:g} seconds'
                           if isinstance(error, TimeoutError) else f'{type(error).__name__}: {error}')[:500]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
