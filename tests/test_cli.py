import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / 'skills/clarity-wiki'


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'old.txt').write_text('온도 -5°C', encoding='utf-8')
        (self.root / 'new.txt').write_text('온도 5°C', encoding='utf-8')

    def run_cli(self, *args, skill=SKILL):
        return subprocess.run(
            [sys.executable, str(skill / 'tools/clarity.py'), *args],
            cwd=self.root, text=True, capture_output=True, timeout=10,
        )

    def test_actual_regression_returns_json_and_findings_exit(self):
        result = self.run_cli('audit', '--root', str(self.root), '--original', 'old.txt', '--revised', 'new.txt')
        self.assertEqual(result.returncode, 1, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'findings')
        self.assertGreater(data['total_findings'], 0)
        self.assertEqual(result.stderr, '')

    def test_colon_subject_swap_returns_context_findings(self):
        (self.root / 'old.txt').write_text('장비A: 10건, 장비B: 20건', encoding='utf-8')
        (self.root / 'new.txt').write_text('장비B: 10건, 장비A: 20건', encoding='utf-8')
        result = self.run_cli('audit', '--root', str(self.root), '--original', 'old.txt', '--revised', 'new.txt')
        self.assertEqual(result.returncode, 1, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'findings')
        self.assertEqual(data['total_findings'], 2)
        self.assertEqual(data['findings'][0]['original']['context'], '장비A')
        self.assertEqual(data['findings'][0]['revised']['context'], '장비B')

    def test_identical_input_returns_no_findings(self):
        result = self.run_cli('audit', '--root', str(self.root), '--original', 'old.txt', '--revised', 'old.txt')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'no_findings')

    def test_invalid_input_is_compact_json(self):
        for args in [
            ('audit', '--root', str(self.root), '--original', '../outside', '--revised', 'new.txt'),
            ('audit', '--root', str(self.root), '--original', 'missing', '--revised', 'new.txt'),
            ('audit', '--root', str(self.root), '--original', 'old.txt', '--revised', 'new.txt', '--limit', '0'),
            ('evidence', '--root', str(self.root)),
        ]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)['status'], 'error')
                self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_copied_skill_runs_from_unrelated_cwd(self):
        copied = self.root / 'copied-skill'
        shutil.copytree(SKILL, copied, ignore=shutil.ignore_patterns('._*', '__pycache__'))
        result = self.run_cli('audit', '--root', str(self.root), '--original', 'old.txt', '--revised', 'new.txt', skill=copied)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['tool'], 'audit_revision')


if __name__ == '__main__':
    unittest.main()
