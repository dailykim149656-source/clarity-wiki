#!/usr/bin/env python3
"""Install the project Skill and local MCP SDK; emit connection JSON on stdout."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


SOURCE_SKILL = Path(__file__).resolve().parents[1] / 'skills/clarity-wiki'
MCP_VERSION = '1.30.0'


class InstallError(Exception):
    """A local installation precondition was not met."""


def _directory_chain(root: Path, relative: Path):
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise InstallError(f'Expected a directory without symlink redirection: {current}')


def _check_venv(skill: Path):
    _directory_chain(skill, Path('.venv/bin'))
    environment = skill / '.venv'
    for directory, names, filenames in os.walk(environment, followlinks=False):
        for name in names + filenames:
            path = Path(directory) / name
            if not path.is_symlink():
                continue
            relative = path.relative_to(environment)
            if relative.parent == Path('bin') and path.is_file():
                if re.fullmatch(r'python(?:3(?:\.\d+)?)?', name):
                    continue
                # Python 3.14's stdlib venv adds this alias on UTF-8 filesystems.
                if name == '\U0001d70bthon' and path.resolve() == (environment / 'bin/python').resolve():
                    continue
            if relative == Path('lib64') and path.resolve() == environment / 'lib' and path.is_dir():
                continue
            raise InstallError(f'Redirected virtual environment path: {path}')


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
    _check_venv(destination)
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


def _run(command: list[str], timeout: int = 180):
    subprocess.run(command, check=True, stdout=sys.stderr, stderr=sys.stderr, timeout=timeout)


def install_mcp(skill: Path) -> Path:
    _check_venv(skill)
    environment = skill / '.venv'
    interpreter = environment / 'bin/python'
    _run([sys.executable, '-m', 'venv', str(environment)], timeout=60)
    _run([str(interpreter), '-m', 'pip', 'install', '--disable-pip-version-check', f'mcp=={MCP_VERSION}'])
    _run([str(interpreter), '-c',
          'from importlib.metadata import version; from mcp.server.fastmcp import FastMCP; '
          f'assert version("mcp") == "{MCP_VERSION}"'], timeout=30)
    return interpreter


def mcp_config(root: Path, skill: Path) -> dict:
    return {'mcpServers': {'clarity-wiki': {
        'command': str(skill / '.venv/bin/python'),
        'args': [str(skill / 'tools/mcp_server.py'), '--root', str(root)],
    }}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Existing project folder; defaults to cwd')
    parser.add_argument('--check', action='store_true', help='Call both MCP tools before emitting connection JSON')
    args = parser.parse_args(argv)
    try:
        if sys.version_info < (3, 10) or os.name != 'posix':
            raise InstallError('Python 3.10+ on POSIX macOS/Linux is required')
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise InstallError('Workspace must be an existing directory')
        skill = install_skill(SOURCE_SKILL, root)
        print(f'[clarity-wiki] Skill installed: {skill}', file=sys.stderr, flush=True)
        interpreter = install_mcp(skill)
        _run([sys.executable, str(skill / 'tools/validate.py')], timeout=30)
        if args.check:
            _run([str(interpreter), str(skill / 'tools/check_mcp.py'), '--root', str(root)], timeout=60)
        print('[clarity-wiki] SDK and Skill validated; register the following JSON in the allowed MCP host.',
              file=sys.stderr, flush=True)
        print(json.dumps(mcp_config(root, skill), ensure_ascii=False, indent=2))
    except (InstallError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        print(f'[clarity-wiki] Installation failed: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
