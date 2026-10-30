#!/usr/bin/env python3
"""Build a reproducible source/plugin ZIP from explicit public directories."""

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ['README.md', 'LICENSE', 'pyproject.toml', 'plugin.json', 'mcp.json',
         'tools/build_release.py', 'docs/USAGE.md', 'docs/VERIFICATION.md']


def public_files():
    files = [ROOT / name for name in FILES]
    for prefix in ['skills/clarity-wiki', 'tests']:
        for path in (ROOT / prefix).rglob('*'):
            parts = path.relative_to(ROOT).parts
            if path.is_symlink():
                raise ValueError('Release source must not contain symlinks')
            if any(part.startswith('.') or part == '__pycache__' or part.endswith('.egg-info') for part in parts):
                continue
            if 'profiles' in parts and path.name != 'generic-technical.md':
                continue
            if path.is_file() and path.suffix in {'.py', '.md', '.json', '.txt', '.csv'}:
                files.append(path)
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing regular release source: {path.relative_to(ROOT)}')
    return sorted(set(files), key=lambda path: path.relative_to(ROOT).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/clarity-wiki-0.3.0.zip')
    args = parser.parse_args()
    files = public_files()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo('clarity-wiki/' + path.relative_to(ROOT).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix + '.sha256').write_text(f'{digest}  {args.output.name}\n', encoding='utf-8')
    print(f'{args.output} | {len(files)} files | sha256 {digest}')


if __name__ == '__main__':
    main()
