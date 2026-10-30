import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


SKILL = Path(__file__).resolve().parents[1] / 'skills/clarity-wiki'
CHECKER = SKILL / 'tools/check_mcp.py'


class MCPCheckCase:
    def setUp(self):
        self.assertTrue(CHECKER.is_file(), 'The installed MCP checker is missing')
        self.temp = tempfile.TemporaryDirectory(prefix='clarity health 한글 ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'task workspace'
        self.root.mkdir()
        (self.root / 'task.txt').write_text('preserve task', encoding='utf-8')

    def run_checker(self, checker=CHECKER, options=(), python_options=()):
        result = subprocess.run([sys.executable, *python_options, str(checker), '--root', str(self.root), *options],
                                cwd=self.base, capture_output=True, text=True, timeout=15)
        report = json.loads(result.stdout)
        self.assertEqual(report['scope'], 'local_stdio')
        self.assertEqual((self.root / 'task.txt').read_text(), 'preserve task')
        self.assertFalse(list(self.root.glob('.clarity-mcp-check-*')), 'Synthetic files leaked')
        return result, report


class MCPCheckTests(MCPCheckCase, unittest.TestCase):
    def test_missing_sdk_fails_without_success_report_or_traceback(self):
        result, report = self.run_checker(python_options=('-S',))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('SDK', report['error'])
        self.assertNotIn('Traceback', result.stderr)

    def test_invalid_workspace_fails_without_creating_it(self):
        missing = self.root / 'missing'
        result, report = self.run_checker(options=('--root', str(missing)))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'failed')
        self.assertFalse(missing.exists())

    def test_timeout_must_be_positive_and_finite(self):
        for value in ('0', '-1', 'nan', 'inf'):
            with self.subTest(value=value):
                result, report = self.run_checker(options=('--timeout', value))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(report['status'], 'failed')


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install .[mcp] to run actual checker transport tests')
class MCPCheckTransportTests(MCPCheckCase, unittest.TestCase):
    def replacement_server(self, code):
        tools = self.base / 'copied skill/tools'
        tools.mkdir(parents=True)
        shutil.copyfile(CHECKER, tools / 'check_mcp.py')
        (tools / 'mcp_server.py').write_text(textwrap.dedent(code), encoding='utf-8')
        return tools / 'check_mcp.py'

    def test_real_server_checks_both_tools_and_cleans_up_on_repeat(self):
        for _ in range(2):
            result, report = self.run_checker()
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(report['status'], 'passed')
            self.assertEqual(report['workspace'], str(self.root))
            checks = {item['name']: item for item in report['checks']}
            self.assertEqual(set(checks), {'initialize', 'tools/list', 'audit_revision', 'check_evidence'})
            self.assertEqual(checks['tools/list']['tools'], ['audit_revision', 'check_evidence'])
            self.assertIn('NUMBER_CHANGED', checks['audit_revision']['rules'])
            self.assertGreater(checks['audit_revision']['total_findings'], 0)
            self.assertEqual(checks['check_evidence']['total_findings'], 0)

    def test_tool_error_cannot_pass(self):
        checker = self.replacement_server('''
            from mcp.server.fastmcp import FastMCP
            server = FastMCP('broken', log_level='ERROR')
            @server.tool()
            def audit_revision(original: str, revised: str, limit: int = 5) -> dict:
                raise ValueError('deliberate tool failure')
            @server.tool()
            def check_evidence(manifest: str, limit: int = 5) -> dict:
                return {'status': 'no_findings', 'total_findings': 0}
            server.run(transport='stdio')
        ''')
        result, report = self.run_checker(checker)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['stage'], 'audit_revision')

    def test_text_only_response_cannot_pass(self):
        checker = self.replacement_server('''
            from mcp.server.fastmcp import FastMCP
            server = FastMCP('broken', log_level='ERROR')
            @server.tool()
            def audit_revision(original: str, revised: str, limit: int = 5) -> str:
                return 'passed'
            @server.tool()
            def check_evidence(manifest: str, limit: int = 5) -> str:
                return 'passed'
            server.run(transport='stdio')
        ''')
        result, report = self.run_checker(checker)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['stage'], 'audit_revision')

    def test_evidence_findings_cannot_pass(self):
        checker = self.replacement_server('''
            from typing import Any
            from mcp.server.fastmcp import FastMCP
            server = FastMCP('broken', log_level='ERROR')
            @server.tool(structured_output=True)
            def audit_revision(original: str, revised: str, limit: int = 5) -> dict[str, Any]:
                return {'status': 'findings', 'total_findings': 1,
                        'findings': [{'rule': 'NUMBER_CHANGED'}]}
            @server.tool(structured_output=True)
            def check_evidence(manifest: str, limit: int = 5) -> dict[str, Any]:
                return {'status': 'findings', 'total_findings': 1, 'findings': [{'rule': 'HASH_MISMATCH'}]}
            server.run(transport='stdio')
        ''')
        result, report = self.run_checker(checker)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['stage'], 'check_evidence')

    def test_audit_without_number_change_rule_cannot_pass(self):
        checker = self.replacement_server('''
            from typing import Any
            from mcp.server.fastmcp import FastMCP
            server = FastMCP('broken', log_level='ERROR')
            @server.tool(structured_output=True)
            def audit_revision(original: str, revised: str, limit: int = 5) -> dict[str, Any]:
                return {'status': 'findings', 'total_findings': 1, 'findings': [{'rule': 'OTHER'}]}
            @server.tool(structured_output=True)
            def check_evidence(manifest: str, limit: int = 5) -> dict[str, Any]:
                return {'status': 'no_findings', 'total_findings': 0, 'findings': []}
            server.run(transport='stdio')
        ''')
        result, report = self.run_checker(checker)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['stage'], 'audit_revision')
        self.assertIn('sign change', report['error'])

    def test_missing_tool_cannot_pass(self):
        checker = self.replacement_server('''
            from mcp.server.fastmcp import FastMCP
            server = FastMCP('broken', log_level='ERROR')
            @server.tool()
            def audit_revision(original: str, revised: str) -> dict:
                return {}
            server.run(transport='stdio')
        ''')
        result, report = self.run_checker(checker)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['stage'], 'tools/list')

    def test_startup_failure_cannot_pass(self):
        checker = self.replacement_server('raise SystemExit(7)\n')
        result, report = self.run_checker(checker)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['stage'], 'initialize')

    def test_timeout_stops_server_and_cleans_up(self):
        pid_file = self.base / 'server.pid'
        checker = self.replacement_server(f'''
            import os
            from pathlib import Path
            import time
            Path({str(pid_file)!r}).write_text(str(os.getpid()))
            time.sleep(60)
        ''')
        result, report = self.run_checker(checker, options=('--timeout', '1'))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('timeout', report['error'].lower())
        pid = int(pid_file.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)


if __name__ == '__main__':
    unittest.main()
