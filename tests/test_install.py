import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


INSTALLER = Path(__file__).resolve().parents[1] / 'tools/install.py'


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(INSTALLER.is_file(), 'The Skill/MCP installer is missing')
        spec = importlib.util.spec_from_file_location('clarity_installer', INSTALLER)
        self.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.installer)
        self.temp = tempfile.TemporaryDirectory(prefix='clarity install ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'source skill'
        (self.source / 'tools').mkdir(parents=True)
        (self.source / 'SKILL.md').write_text('---\nname: clarity-wiki\ndescription: test fixture\n---\n', encoding='utf-8')
        (self.source / 'tools/validate.py').write_text('print("fixture validation")\n', encoding='utf-8')
        self.root = self.base / 'work project'
        self.root.mkdir()
        self.destination = self.root / '.agents/skills/clarity-wiki'

    def test_copies_skill_to_explicit_project_with_spaces(self):
        (self.root / 'task.txt').write_text('keep', encoding='utf-8')
        result = self.installer.install_skill(self.source, self.root)
        self.assertEqual(result, self.destination)
        self.assertEqual((result / 'SKILL.md').read_bytes(), (self.source / 'SKILL.md').read_bytes())
        self.assertTrue((result / 'tools/validate.py').is_file())
        self.assertEqual((self.root / 'task.txt').read_text(), 'keep')

    def test_repeat_install_updates_bundled_files_preserving_notes_and_venv(self):
        self.installer.install_skill(self.source, self.root)
        (self.destination / 'notes.txt').write_text('personal note', encoding='utf-8')
        (self.destination / '.venv/bin').mkdir(parents=True)
        (self.destination / '.venv/bin/python').symlink_to(sys.executable)
        (self.source / 'tools/validate.py').write_text('print("updated")\n', encoding='utf-8')
        self.installer.install_skill(self.source, self.root)
        self.assertEqual((self.destination / 'tools/validate.py').read_text(), 'print("updated")\n')
        self.assertEqual((self.destination / 'notes.txt').read_text(), 'personal note')
        self.assertTrue((self.destination / '.venv/bin/python').is_symlink())
        self.assertFalse((self.destination / 'clarity-wiki').exists())

    def test_unrelated_existing_directory_is_preserved(self):
        self.destination.mkdir(parents=True)
        sentinel = self.destination / 'unrelated.txt'
        sentinel.write_text('keep', encoding='utf-8')
        with self.assertRaises(self.installer.InstallError):
            self.installer.install_skill(self.source, self.root)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertFalse((self.destination / 'SKILL.md').exists())

    def test_reuses_python_314_venv_alias(self):
        self.installer.install_skill(self.source, self.root)
        binaries = self.destination / '.venv/bin'
        binaries.mkdir(parents=True)
        (binaries / 'python').symlink_to(sys.executable)
        alias = binaries / '\U0001d70bthon'
        alias.symlink_to('python')
        self.assertEqual(self.installer.install_skill(self.source, self.root), self.destination)
        self.assertTrue(alias.is_symlink())

    def test_rejects_redirected_destination_ancestors_and_files(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.root / '.agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(self.installer.InstallError):
            self.installer.install_skill(self.source, self.root)
        self.assertEqual(list(outside.iterdir()), [])
        (self.root / '.agents').unlink()
        self.installer.install_skill(self.source, self.root)
        target = outside / 'sentinel.py'
        target.write_text('keep', encoding='utf-8')
        launcher = self.destination / 'tools/validate.py'
        launcher.unlink()
        launcher.symlink_to(target)
        with self.assertRaises(self.installer.InstallError):
            self.installer.install_skill(self.source, self.root)
        self.assertEqual(target.read_text(), 'keep')

    def test_rejects_redirected_venv_directory(self):
        self.installer.install_skill(self.source, self.root)
        outside = self.base / 'other venv'
        outside.mkdir()
        (self.destination / '.venv').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(self.installer.InstallError):
            self.installer.install_skill(self.source, self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_redirected_venv_config_cannot_overwrite_external_file(self):
        self.installer.install_skill(self.source, self.root)
        environment = self.destination / '.venv'
        environment.mkdir()
        sentinel = self.base / 'outside config.txt'
        sentinel.write_text('keep external config', encoding='utf-8')
        (environment / 'pyvenv.cfg').symlink_to(sentinel)

        def allow_venv_without_network(command, timeout=180):
            if command[1:3] == ['-m', 'venv']:
                subprocess.run(command, check=True, capture_output=True, timeout=60)
            else:
                raise self.installer.InstallError('Stop before package download')

        with patch.object(self.installer, '_run', side_effect=allow_venv_without_network), \
                self.assertRaises(self.installer.InstallError):
            self.installer.install_mcp(self.destination)
        self.assertEqual(sentinel.read_text(), 'keep external config')

    def test_rejects_source_destination_overlap(self):
        with self.assertRaises(self.installer.InstallError):
            self.installer.install_skill(self.source, self.source)
        self.assertFalse((self.source / '.agents').exists())

    def test_excludes_private_profiles_caches_and_hidden_source_files(self):
        for name in ['.venv/secret', '._metadata', '__pycache__/cache.pyc', 'profiles/author-default.md']:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('private', encoding='utf-8')
        (self.source / 'profiles/generic-technical.md').write_text('public', encoding='utf-8')
        self.installer.install_skill(self.source, self.root)
        for name in ['.venv', '._metadata', '__pycache__', 'profiles/author-default.md']:
            self.assertFalse((self.destination / name).exists(), name)
        self.assertEqual((self.destination / 'profiles/generic-technical.md').read_text(), 'public')

    def test_rejects_symlink_in_public_source(self):
        (self.source / 'tools/link.py').symlink_to(self.source / 'tools/validate.py')
        with self.assertRaises(self.installer.InstallError):
            self.installer.install_skill(self.source, self.root)
        self.assertFalse(self.destination.exists())

    def test_config_uses_absolute_venv_path_without_resolving_interpreter(self):
        self.installer.install_skill(self.source, self.root)
        (self.destination / '.venv/bin').mkdir(parents=True)
        interpreter = self.destination / '.venv/bin/python'
        interpreter.symlink_to(sys.executable)
        settings = self.installer.mcp_config(self.root, self.destination)['mcpServers']['clarity-wiki']
        self.assertEqual(settings['command'], str(interpreter))
        self.assertEqual(settings['args'], [str(self.destination / 'tools/mcp_server.py'), '--root', str(self.root)])

    def test_sdk_failure_produces_no_success_json_and_keeps_skill(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(self.installer, 'SOURCE_SKILL', self.source), \
                patch.object(self.installer, 'install_mcp', side_effect=self.installer.InstallError('SDK unavailable')), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.installer.main(['--root', str(self.root)])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('SDK unavailable', stderr.getvalue())
        self.assertTrue((self.destination / 'SKILL.md').is_file())

    def test_failed_post_install_check_produces_no_connection_json(self):
        (self.source / 'tools/check_mcp.py').write_text(
            'from pathlib import Path\nPath(__file__).with_suffix(".ran").write_text("called")\nraise SystemExit(2)\n',
            encoding='utf-8')
        stdout = io.StringIO()
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stderr, \
                patch.object(self.installer, 'SOURCE_SKILL', self.source), \
                patch.object(self.installer, 'install_mcp', return_value=Path(sys.executable)), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.installer.main(['--root', str(self.root), '--check'])
            stderr.seek(0)
            message = stderr.read()
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('Installation failed', message)
        self.assertTrue((self.destination / 'tools/check_mcp.ran').is_file())
        self.assertTrue((self.destination / 'SKILL.md').is_file())

    def test_invalid_workspace_produces_no_json(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.installer.main(['--root', str(self.root / 'missing')])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertTrue(stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
