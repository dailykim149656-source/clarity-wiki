#!/usr/bin/env python3
"""Offline Skill frontmatter and internal-link validation."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote

BASE = Path(__file__).resolve().parents[1]


def validate(base=BASE):
    errors = []
    try:
        text = (base / 'SKILL.md').read_text(encoding='utf-8')
        front = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, flags=re.S)
        if not front:
            errors.append('SKILL.md: missing YAML frontmatter')
        else:
            if not re.search(r'^name:\s*clarity-wiki\s*$', front[1], flags=re.M):
                errors.append('SKILL.md: name must be clarity-wiki')
            if not re.search(r'^description:\s*\S+', front[1], flags=re.M):
                errors.append('SKILL.md: description is required')
        for path in sorted(base.rglob('*.md')):
            if any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(base).parts):
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
                errors.append(f'{path.name}: symlink outside regular Skill source')
                continue
            source = path.read_text(encoding='utf-8')
            for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', source):
                target = target.strip('<>')
                if target.startswith(('https://', 'http://', '#', 'mailto:')):
                    continue
                local = (path.parent / unquote(target.split('#')[0])).resolve()
                if not local.is_file() or not local.is_relative_to(base.resolve()):
                    errors.append(f'{path.relative_to(base)}: missing or escaping link {target}')
    except (OSError, UnicodeError) as error:
        errors.append(f'cannot read Skill source: {type(error).__name__}')
    return errors


if __name__ == '__main__':
    problems = validate()
    if problems:
        print('\n'.join(problems))
        sys.exit(1)
    print('PASS | Skill frontmatter and internal links | AppleDouble excluded | offline')
