import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/clarity-wiki/scripts'))

from clarity_wiki.workspace import InputError, Workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        self.workspace = Workspace(self.root)

    def test_reads_utf8_and_normalizes_relative_path(self):
        (self.root / 'input.txt').write_text('온도 -5°C', encoding='utf-8')
        self.assertEqual(self.workspace.read_text('input.txt'), '온도 -5°C')
        self.assertEqual(self.workspace.relative(self.root / 'input.txt'), 'input.txt')

    def test_rejects_traversal_and_external_symlink(self):
        outside = Path(self.temp.name) / 'outside.txt'
        outside.write_text('private', encoding='utf-8')
        (self.root / 'link.txt').symlink_to(outside)
        for name in ['../outside.txt', outside, 'link.txt']:
            with self.subTest(name=name), self.assertRaises(InputError):
                self.workspace.read_text(name)

    def test_rejects_missing_directory_and_fifo_without_blocking(self):
        with self.assertRaises(InputError):
            self.workspace.read_bytes('missing')
        with self.assertRaises(InputError):
            self.workspace.read_bytes('.')
        if hasattr(os, 'mkfifo'):
            os.mkfifo(self.root / 'pipe')
            with self.assertRaises(InputError):
                self.workspace.read_bytes('pipe')

    def test_rejects_oversize_and_invalid_utf8(self):
        (self.root / 'input.txt').write_bytes(b'12345')
        with self.assertRaises(InputError):
            self.workspace.read_bytes('input.txt', max_bytes=4)
        (self.root / 'input.txt').write_bytes(b'\xff')
        with self.assertRaises(InputError):
            self.workspace.read_text('input.txt')

    def test_root_must_be_existing_directory(self):
        with self.assertRaises(InputError):
            Workspace(self.root / 'missing')
        f = self.root / 'file'
        f.write_bytes(b'')
        with self.assertRaises(InputError):
            Workspace(f)

    def test_directory_swap_between_resolution_and_open_cannot_escape(self):
        directory = self.root / 'sub'
        directory.mkdir()
        (directory / 'file.txt').write_text('inside', encoding='utf-8')
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (outside / 'file.txt').write_text('outside sentinel', encoding='utf-8')
        resolve = self.workspace._resolve

        def replace_after_resolution(path):
            resolved = resolve(path)
            directory.rename(self.root / 'original-sub')
            directory.symlink_to(outside, target_is_directory=True)
            return resolved

        with patch.object(self.workspace, '_resolve', side_effect=replace_after_resolution):
            with self.assertRaises(InputError):
                self.workspace.read_text('sub/file.txt')


if __name__ == '__main__':
    unittest.main()
