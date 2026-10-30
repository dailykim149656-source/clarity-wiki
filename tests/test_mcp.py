import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
LAUNCHER = REPO / 'skills/clarity-wiki/tools/mcp_server.py'


class MCPStartupTests(unittest.TestCase):
    def test_root_is_required_and_environment_root_must_be_absolute(self):
        for value in [None, '.']:
            env = os.environ.copy()
            env.pop('CLARITY_WORKSPACE_ROOT', None)
            if value is not None:
                env['CLARITY_WORKSPACE_ROOT'] = value
            result = subprocess.run([sys.executable, str(LAUNCHER)], env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('workspace', result.stderr.lower())
            self.assertNotIn('Traceback', result.stderr)


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install .[mcp] to run real stdio transport tests')
class MCPTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_tools_calls_and_boundary_error(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def scenario():
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'old.txt').write_text('온도 -5°C', encoding='utf-8')
                (root / 'new.txt').write_text('온도 5°C', encoding='utf-8')
                (root / 'result.txt').write_text('synthetic result', encoding='utf-8')
                digest = lambda name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                document = {'version': 1, 'artifacts': ['result.txt'], 'requirements': [{
                    'id': 'R1', 'criterion': 'synthetic format check', 'status': 'verified',
                    'evidence': [{'path': 'result.txt', 'sha256': digest('result.txt'),
                                  'command': 'not executed', 'exit_code': 0,
                                  'inputs': [{'path': 'old.txt', 'sha256': digest('old.txt')}]}],
                }]}
                (root / 'manifest.json').write_text(json.dumps(document), encoding='utf-8')
                parameters = StdioServerParameters(command=sys.executable,
                    args=[str(LAUNCHER), '--root', str(root)], env={'PYTHONDONTWRITEBYTECODE': '1'})
                async with stdio_client(parameters) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = (await session.list_tools()).tools
                        self.assertEqual({tool.name for tool in tools}, {'audit_revision', 'check_evidence'})
                        for tool in tools:
                            self.assertTrue(tool.annotations.readOnlyHint)
                            self.assertFalse(tool.annotations.openWorldHint)
                        result = await session.call_tool('audit_revision', {'original': 'old.txt', 'revised': 'new.txt'})
                        self.assertFalse(result.isError)
                        self.assertEqual(result.structuredContent['status'], 'findings')
                        self.assertGreater(result.structuredContent['total_findings'], 0)
                        evidence = await session.call_tool('check_evidence', {'manifest': 'manifest.json'})
                        self.assertFalse(evidence.isError)
                        self.assertEqual(evidence.structuredContent['status'], 'no_findings')
                        for arguments in [
                            {'original': '../private.txt', 'revised': 'new.txt'},
                            {'original': 'old.txt', 'revised': 'new.txt', 'limit': 31},
                        ]:
                            error = await session.call_tool('audit_revision', arguments)
                            self.assertTrue(error.isError)
                        self.assertEqual((root / 'old.txt').read_text(), '온도 -5°C')
        await asyncio.wait_for(scenario(), timeout=20)


if __name__ == '__main__':
    unittest.main()
