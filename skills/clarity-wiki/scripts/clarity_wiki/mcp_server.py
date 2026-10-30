"""Optional SDK stdio adapter; the workspace is fixed at startup."""

import argparse
import os
from pathlib import Path
import sys
from typing import Annotated, Any

from .workspace import InputError, Workspace


def build_server(workspace: Workspace):
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.server.fastmcp.exceptions import ToolError
        from mcp.types import ToolAnnotations
        from pydantic import Field
    except ImportError as error:
        raise InputError("MCP SDK missing: install this package with pip install '.[mcp]' in the server's Python environment") from error

    from .audit import audit_revision as inspect_revision
    from .evidence import check_evidence as inspect_evidence

    server = FastMCP('clarity-wiki', log_level='ERROR', instructions=(
        'Read-only heuristic file checks inside the startup workspace. '
        'No findings does not prove correctness or execution. No shell, network, or writes.'))
    annotations = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                  idempotentHint=True, openWorldHint=False)

    @server.tool(annotations=annotations, structured_output=True)
    def audit_revision(original: str, revised: str,
                       limit: Annotated[int, Field(ge=1, le=30, strict=True)] = 5) -> dict[str, Any]:
        """Flag numeric, unit and quote revision candidates in two workspace-relative UTF-8 files."""
        try:
            return inspect_revision(workspace, original, revised, limit)
        except InputError as error:
            raise ToolError(str(error)[:500]) from None

    @server.tool(annotations=annotations, structured_output=True)
    def check_evidence(manifest: str,
                       limit: Annotated[int, Field(ge=1, le=30, strict=True)] = 5) -> dict[str, Any]:
        """Check declared manifest-v1 evidence and file hashes; never execute or certify commands."""
        try:
            return inspect_evidence(workspace, manifest, limit)
        except InputError as error:
            raise ToolError(str(error)[:500]) from None

    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description='Clarity Wiki read-only stdio MCP; explicit workspace required.')
    parser.add_argument('--root', help='Allowed workspace root (or absolute CLARITY_WORKSPACE_ROOT).')
    args = parser.parse_args(argv)
    root = args.root or os.environ.get('CLARITY_WORKSPACE_ROOT')
    if not root:
        parser.error('workspace is required: pass --root or set absolute CLARITY_WORKSPACE_ROOT')
    if not args.root and not Path(root).is_absolute():
        parser.error('CLARITY_WORKSPACE_ROOT must be an absolute workspace path')
    try:
        workspace = Workspace(root)
        try:
            build_server(workspace).run(transport='stdio')
        finally:
            workspace.close()
    except InputError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
