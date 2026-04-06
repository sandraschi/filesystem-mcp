"""Git administrative tools — DEPRECATED 2026-04-06.

These tools have been consolidated into gitops (git-github-mcp).
Use gitops:git_ops for all local git operations.
Use gitops:github_ops for all GitHub operations.

This file is kept as a stub to avoid import errors.
The @_app.tool() registrations are intentionally absent — tools removed from MCP surface.
"""

from __future__ import annotations

# Intentionally empty — git tools removed from fileops.
# All git operations: use gitops:git_ops (git-github-mcp server).
# branch_rename: git_ops(operation='branch_rename', branch='old', source_branch='new', repo_path='...')
