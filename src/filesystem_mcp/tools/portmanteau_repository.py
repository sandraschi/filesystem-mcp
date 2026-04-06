"""Git repository operations — DEPRECATED 2026-04-06.

Consolidated into gitops (git-github-mcp).
Use gitops:git_ops for all local git operations.

This file is kept as a stub to avoid import errors.
"""

from __future__ import annotations

# Intentionally empty — repo_ops removed from fileops.
# Use gitops:git_ops instead:
#   status:         git_ops(operation='status', repo_path='...')
#   commit:         git_ops(operation='commit', message='...', all_files=True, repo_path='...')
#   log:            git_ops(operation='log', repo_path='...')
#   diff:           git_ops(operation='diff', repo_path='...')
#   clone:          git_ops(operation='clone', repo_url='...', target_dir='...')
#   init:           git_ops(operation='init', repo_path='...')
#   reset:          git_ops(operation='reset', mode='hard', commit='HEAD~1', repo_path='...')
#   revert:         git_ops(operation='revert', commit='abc123', repo_path='...')
#   cherry_pick:    git_ops(operation='cherry_pick', commit='abc123', repo_path='...')
#   blame:          git_ops(operation='blame', file_path='src/foo.py', repo_path='...')
