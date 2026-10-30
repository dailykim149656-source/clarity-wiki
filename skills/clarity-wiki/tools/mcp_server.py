#!/usr/bin/env python3
"""Launch the optional MCP adapter from a copied Skill."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from clarity_wiki.mcp_server import main

if __name__ == '__main__':
    raise SystemExit(main())
