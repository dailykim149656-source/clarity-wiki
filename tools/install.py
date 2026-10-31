#!/usr/bin/env python3
"""Copy and validate the project Skill with its bundled, dependency-free CLI."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


SOURCE_SKILL = Path(__file__).resolve().parents[1] / 'skills/clarity-wiki'


class InstallError(Exception):
    """A local installation precondition was not met."""


def _directory_chain(root: Path, relative: Path):
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise InstallError(f'Expected a directory without symlink redirection: {current}')


def _source_files(source: Path) -> list[Path]:
    files = []
    for directory, names, filenames in os.walk(source, followlinks=False):
        parent = Path(directory)
        names[:] = [name for name in names if not name.startswith('.')
                    and name not in {'__pycache__', '__MACOSX'} and not name.endswith('.egg-info')]
        for name in names:
            if (parent / name).is_symlink():
                raise InstallError(f'Symlink in public Skill source: {parent / name}')
        for name in filenames:
            path = parent / name
            relative = path.relative_to(source)
            if name.startswith('.') or path.suffix not in {'.py', '.md', '.json', '.txt', '.csv'}:
                continue
            if 'profiles' in relative.parts and relative.as_posix() != 'profiles/generic-technical.md':
                continue
            if path.is_symlink() or not path.is_file():
                raise InstallError(f'Expected a regular public source file: {path}')
            files.append(relative)
    return sorted(files)


def install_skill(source: Path, root: Path) -> Path:
    root = root.resolve(strict=True)
    if not root.is_dir() or source.is_symlink() or not source.is_dir():
        raise InstallError('Source Skill and workspace must be existing directories')
    source = source.resolve(strict=True)
    destination = root / '.agents/skills/clarity-wiki'
    if source == destination or source in destination.parents or destination in source.parents:
        raise InstallError('Source and installed Skill directories must not overlap')
    _directory_chain(root, destination.relative_to(root))
    skill_file = destination / 'SKILL.md'
    if skill_file.is_symlink():
        raise InstallError(f'SKILL.md must not be a symlink: {skill_file}')
    if destination.exists() and any(destination.iterdir()):
        if not skill_file.is_file() or not re.search(
                r'^name:\s*clarity-wiki\s*$', skill_file.read_text(encoding='utf-8'), re.M):
            raise InstallError(f'Refusing to overwrite an unrelated directory: {destination}')
    if not (source / 'SKILL.md').is_file():
        raise InstallError('Source SKILL.md is missing')
    files = _source_files(source)
    for relative in files:
        target = destination / relative
        _directory_chain(root, target.parent.relative_to(root))
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise InstallError(f'Refusing to replace a non-regular destination: {target}')
    for relative in files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    return destination


def _run(command: list[str], timeout: int = 30):
    subprocess.run(command, check=True, stdout=sys.stderr, stderr=sys.stderr, timeout=timeout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Existing project folder; defaults to cwd')
    args = parser.parse_args(argv)
    try:
        if sys.version_info < (3, 10) or os.name != 'posix':
            raise InstallError('Python 3.10+ on POSIX macOS/Linux is required')
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise InstallError('Workspace must be an existing directory')
        skill = install_skill(SOURCE_SKILL, root)
        print(f'[clarity-wiki] Skill installed: {skill}', file=sys.stderr, flush=True)
        _run([sys.executable, '-I', '-S', str(skill / 'tools/validate.py')])
        _run([sys.executable, '-I', '-S', str(skill / 'tools/clarity.py'), '--version'])
        print('[clarity-wiki] Skill and bundled CLI validated; no dependencies required.',
              file=sys.stderr, flush=True)
    except (InstallError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        print(f'[clarity-wiki] Installation failed: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
