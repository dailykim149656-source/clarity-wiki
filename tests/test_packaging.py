import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_skill_validation_ignores_appledouble(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / 'skill'
            shutil.copytree(REPO / 'skills/clarity-wiki', skill,
                            ignore=shutil.ignore_patterns('._*', '__pycache__'))
            (skill / '._README.md').write_bytes(b'\xff\x00AppleDouble')
            result = subprocess.run([sys.executable, str(skill / 'tools/validate.py')],
                                    cwd=directory, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_plugin_manifest_has_only_local_stdio_transport(self):
        plugin = json.loads((REPO / 'plugin.json').read_text())
        self.assertEqual(plugin['name'], 'clarity-wiki')
        self.assertEqual(plugin['version'], '0.3.0')
        mcp = json.loads((REPO / 'mcp.json').read_text())['mcpServers']
        self.assertEqual(list(mcp), ['clarity-wiki'])
        self.assertEqual(mcp['clarity-wiki']['type'], 'stdio')
        self.assertNotIn('url', mcp['clarity-wiki'])

    def test_release_is_reproducible_and_excludes_local_material(self):
        with tempfile.TemporaryDirectory() as directory:
            archives = []
            for name in ['one.zip', 'two.zip']:
                target = Path(directory) / name
                result = subprocess.run([sys.executable, str(REPO / 'tools/build_release.py'), '--output', str(target)],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                archives.append(target)
            self.assertEqual(archives[0].read_bytes(), archives[1].read_bytes())
            with zipfile.ZipFile(archives[0]) as archive:
                names = archive.namelist()
                self.assertIn('clarity-wiki/plugin.json', names)
                self.assertIn('clarity-wiki/START_HERE.md', names)
                self.assertIn('clarity-wiki/skills/clarity-wiki/SKILL.md', names)
                self.assertIn('clarity-wiki/skills/clarity-wiki/examples/workflow-cases.md', names)
                self.assertIn('clarity-wiki/skills/clarity-wiki/scripts/clarity_wiki/audit.py', names)
                for name in names:
                    self.assertFalse(any(part.startswith('._') or part in {'.omo', '__pycache__'} for part in Path(name).parts), name)
                    self.assertNotIn('author-default.md', name)
                    self.assertNotIn('.egg-info', name)
                    self.assertFalse(name.endswith(('.pdf', '.zip', '.pyc')), name)
                archive.extractall(Path(directory) / 'extracted')
            extracted = Path(directory) / 'extracted/clarity-wiki'
            result = subprocess.run([sys.executable, str(extracted / 'skills/clarity-wiki/tools/validate.py')],
                                    cwd=directory, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
