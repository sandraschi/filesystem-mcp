"""Git administrative tools — one tool per operation (no portmanteau enum).

Response shape (success): success, operation, result (operation-specific dict),
timestamp, quality_metrics, recommendations, next_steps, related_operations.
Error shape: success=False, error, error_type, recovery_options, timestamp, diagnostic_info.
"""

from __future__ import annotations

import logging
from typing import Any

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _success_response,
)

logger = logging.getLogger(__name__)

_git = None


def _get_git():
    global _git
    if _git is None:
        try:
            import git as git_module

            _git = git_module
        except ImportError as e:
            raise RuntimeError(
                "Git operations require 'GitPython'. Install with: pip install GitPython"
            ) from e
    return _git


# Shared documentation fragment for LLM consumers
def _git_merge_recovery(message: str) -> list[str]:
    m = message.lower()
    if "conflict" in m or "merge conflict" in m:
        return [
            "Run git_resolve_conflicts(repo_path=...) to list unmerged file paths.",
            "Edit conflict markers in the working tree, then repo_ops(operation='commit_changes', ...) to finish the merge.",
            "To cancel the merge: use the git CLI `git merge --abort` (not wrapped as a dedicated tool here).",
        ]
    return [
        "Confirm source_branch exists (git_list_branches) and the working tree is clean or stashed (git_stash_changes).",
        "Run git_fetch_updates(repo_path=..., remote_name=...) then retry.",
        "Verify repo_path points to the repository root (directory containing .git).",
    ]


def _git_push_recovery(message: str) -> list[str]:
    m = message.lower()
    if "rejected" in m or "non-fast-forward" in m:
        return [
            "Run git_fetch_updates then git_pull_changes or rebase locally before pushing.",
            "If you intend to overwrite remote history (dangerous), use git_push_changes(..., force_push=True) only after verifying no collaborators rely on the old commits.",
        ]
    return [
        "Check network and remote_name; use git_list_remotes(repo_path=...).",
        "Verify authentication and that push_branch matches the branch you intend to publish.",
    ]


async def _rename_branch(repo_path: str, old_name: str, new_name: str) -> dict[str, Any]:
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        repo.git.branch("-m", old_name, new_name)
        return _success_response(
            {"renamed_from": old_name, "renamed_to": new_name},
            next_steps=[f"git_switch_branch(repo_path='{repo_path}', branch_name='{new_name}')"],
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _create_branch(repo_path: str, branch_name: str) -> dict[str, Any]:
    """Create a new local branch pointing at the current HEAD (does not switch).

    Idempotency: not idempotent — if branch_name already exists, Git raises; safe to retry only after renaming or deleting the conflicting branch.
    """
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        repo.create_head(branch_name)
        return _success_response(
            {"branch": branch_name},
            next_steps=[f"git_switch_branch(repo_path='{repo_path}', branch_name='{branch_name}')"],
        )
    except Exception as e:
        err = str(e)
        if "already exists" in err.lower():
            return _error_response(
                err,
                "git_error",
                recovery_options=[
                    "Branch already exists: use git_switch_branch to check it out, or delete/rename the old branch first.",
                    "List branches with git_list_branches(repo_path=...).",
                ],
            )
        return _error_response(err, "git_error")


async def _switch_branch(repo_path: str, branch_name: str) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).git.checkout(branch_name)
        return _success_response({"switched_to": branch_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _merge_branch(repo_path: str, source: str, target: str | None) -> dict[str, Any]:
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        if target:
            repo.git.checkout(target)
        repo.git.merge(source)
        return _success_response({"merged": source})
    except Exception as e:
        return _error_response(str(e), "git_error", recovery_options=_git_merge_recovery(str(e)))


async def _delete_branch(repo_path: str, branch_name: str, force_delete: bool) -> dict[str, Any]:
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        repo.git.branch("-D" if force_delete else "-d", branch_name)
        return _success_response({"deleted": branch_name})
    except Exception as e:
        return _error_response(
            str(e),
            "git_error",
            recovery_options=[
                "If delete was refused due to unmerged work, merge or use force_delete=True (drops commits not merged elsewhere — destructive).",
                "Verify branch_name exists: git_list_branches(repo_path=...).",
            ],
        )


async def _list_branches(repo_path: str) -> dict[str, Any]:
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        return _success_response(
            {
                "local": [b.name for b in repo.branches],
                "active": repo.active_branch.name,
            },
            next_steps=[
                "git_switch_branch(repo_path=..., branch_name='...')",
                "git_merge_branch(repo_path=..., source_branch='...')",
            ],
            related_operations=["git_list_tags", "git_list_remotes"],
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _create_tag(repo_path: str, tag_name: str, message: str | None) -> dict[str, Any]:
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        repo.create_tag(tag_name, message=message)
        return _success_response({"tag": tag_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_tags(repo_path: str) -> dict[str, Any]:
    try:
        git = _get_git()
        return _success_response({"tags": [t.name for t in git.Repo(repo_path).tags]})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _delete_tag(repo_path: str, tag_name: str) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).delete_tag(tag_name)
        return _success_response({"deleted": tag_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _push_changes(
    repo_path: str, remote: str, branch: str | None, force_push: bool
) -> dict[str, Any]:
    try:
        git = _get_git()
        r = git.Repo(repo_path).remote(remote)
        if branch:
            r.push(branch, force=force_push)
        else:
            r.push(force=force_push)
        return _success_response({"status": "pushed"})
    except Exception as e:
        return _error_response(
            str(e), "git_error", recovery_options=_git_push_recovery(str(e))
        )


async def _pull_changes(repo_path: str, remote: str, branch: str | None) -> dict[str, Any]:
    try:
        git = _get_git()
        r = git.Repo(repo_path).remote(remote)
        if branch:
            r.pull(branch)
        else:
            r.pull()
        return _success_response({"status": "pulled"})
    except Exception as e:
        return _error_response(
            str(e),
            "git_error",
            recovery_options=_git_merge_recovery(str(e))
            + [
                "If pull failed mid-merge, resolve conflicts then commit; or abort merge via git CLI.",
            ],
        )


async def _fetch_updates(repo_path: str, remote: str) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).remote(remote).fetch()
        return _success_response({"status": "fetched"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_remotes(repo_path: str) -> dict[str, Any]:
    try:
        git = _get_git()
        return _success_response(
            {
                "remotes": [
                    {"name": r.name, "urls": list(r.urls)} for r in git.Repo(repo_path).remotes
                ],
            }
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _add_remote(repo_path: str, name: str, url: str) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).create_remote(name, url)
        return _success_response({"remote": name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _remove_remote(repo_path: str, name: str) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).delete_remote(name)
        return _success_response({"status": "removed"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _stash_changes(repo_path: str, message: str | None) -> dict[str, Any]:
    try:
        git = _get_git()
        repo = git.Repo(repo_path)
        if message:
            repo.git.stash("push", "-m", message)
        else:
            repo.git.stash("push")
        return _success_response({"status": "stashed"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _apply_stash(repo_path: str, index: int) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).git.stash("apply", f"stash@{{{index}}}")
        return _success_response({"status": "applied"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_stashes(repo_path: str) -> dict[str, Any]:
    try:
        git = _get_git()
        stashes = git.Repo(repo_path).git.stash("list").split("\n")
        return _success_response({"stashes": stashes})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _resolve_conflicts(repo_path: str) -> dict[str, Any]:
    try:
        git = _get_git()
        unmerged = git.Repo(repo_path).git.diff("--name-only", "--diff-filter=U").split("\n")
        return _success_response({"conflicted": [u for u in unmerged if u.strip()]})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _rebase_branch(repo_path: str, source: str) -> dict[str, Any]:
    try:
        _get_git().Repo(repo_path).git.rebase(source)
        return _success_response({"status": "rebased"})
    except Exception as e:
        return _error_response(
            str(e),
            "git_error",
            recovery_options=[
                "If rebase stopped with conflicts: resolve files, `git rebase --continue`, or `git rebase --abort` via CLI.",
                "Ensure source_branch is fetched: git_fetch_updates(repo_path=...).",
            ],
        )


_app = _get_app()


@_app.tool()
async def git_create_branch(repo_path: str, branch_name: str) -> dict[str, Any]:
    """Create a new local branch at the current HEAD (does not check out).

    Recovery: On failure, see error message; if branch exists, switch or delete first.

    Idempotency: Fails if branch_name already exists — not safe to blindly retry.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"branch": str}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    if not branch_name:
        return _clarification_response("branch_name", "branch_name is required", [])
    try:
        return await _create_branch(repo_path, branch_name)
    except Exception as e:
        logger.exception("git_create_branch failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_rename_branch(
    repo_path: str, branch_name: str, target_branch: str
) -> dict[str, Any]:
    """Rename a branch (git branch -m old new).

    Args:
        repo_path: Repository root path.
        branch_name: Current branch name.
        target_branch: New branch name.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"renamed_from": str, "renamed_to": str}
    """
    if not repo_path or not branch_name or not target_branch:
        return _clarification_response(
            "params", "repo_path, branch_name (old), and target_branch (new) are required", []
        )
    try:
        return await _rename_branch(repo_path, branch_name, target_branch)
    except Exception as e:
        logger.exception("git_rename_branch failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_switch_branch(repo_path: str, branch_name: str) -> dict[str, Any]:
    """Check out an existing branch.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"switched_to": str}
    """
    if not repo_path or not branch_name:
        return _clarification_response("params", "repo_path and branch_name are required", [])
    try:
        return await _switch_branch(repo_path, branch_name)
    except Exception as e:
        logger.exception("git_switch_branch failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_merge_branch(
    repo_path: str,
    source_branch: str,
    target_branch: str | None = None,
) -> dict[str, Any]:
    """Merge source_branch into the current branch (or into target_branch if provided).

    Recovery: On merge conflicts, resolve files then commit; see git_resolve_conflicts.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"merged": str} — name of the branch merged in.
    """
    if not repo_path or not source_branch:
        return _clarification_response(
            "params", "repo_path and source_branch are required", []
        )
    try:
        return await _merge_branch(repo_path, source_branch, target_branch)
    except Exception as e:
        logger.exception("git_merge_branch failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_delete_branch(
    repo_path: str,
    branch_name: str,
    force_delete: bool = False,
) -> dict[str, Any]:
    """Delete a local branch (-d safe, -D if force_delete).

    Args:
        force_delete: If True, use -D (delete even if not merged — can lose commits only on that branch).

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"deleted": str}
    """
    if not repo_path or not branch_name:
        return _clarification_response("params", "repo_path and branch_name are required", [])
    try:
        return await _delete_branch(repo_path, branch_name, force_delete)
    except Exception as e:
        logger.exception("git_delete_branch failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_list_branches(repo_path: str) -> dict[str, Any]:
    """List local branches and the active branch.

    Idempotency: Read-only; safe to retry.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"local": list[str], "active": str}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _list_branches(repo_path)
    except Exception as e:
        logger.exception("git_list_branches failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_create_tag(
    repo_path: str,
    tag_name: str,
    tag_message: str | None = None,
) -> dict[str, Any]:
    """Create an annotated or lightweight tag (message optional).

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"tag": str}
    """
    if not repo_path or not tag_name:
        return _clarification_response("params", "repo_path and tag_name are required", [])
    try:
        return await _create_tag(repo_path, tag_name, tag_message)
    except Exception as e:
        logger.exception("git_create_tag failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_list_tags(repo_path: str) -> dict[str, Any]:
    """List all tag names.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"tags": list[str]}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _list_tags(repo_path)
    except Exception as e:
        logger.exception("git_list_tags failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_delete_tag(repo_path: str, tag_name: str) -> dict[str, Any]:
    """Delete a local tag.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"deleted": str}
    """
    if not repo_path or not tag_name:
        return _clarification_response("params", "repo_path and tag_name are required", [])
    try:
        return await _delete_tag(repo_path, tag_name)
    except Exception as e:
        logger.exception("git_delete_tag failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_push_changes(
    repo_path: str,
    remote_name: str = "origin",
    push_branch: str | None = None,
    force_push: bool = False,
) -> dict[str, Any]:
    """Push commits to a remote.

    Args:
        force_push: If True, force non-fast-forward updates (can overwrite remote history — use only when intended).

    Recovery: On non-fast-forward, fetch and merge/rebase before pushing.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "pushed"}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _push_changes(repo_path, remote_name, push_branch, force_push)
    except Exception as e:
        logger.exception("git_push_changes failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_pull_changes(
    repo_path: str,
    remote_name: str = "origin",
    pull_branch: str | None = None,
) -> dict[str, Any]:
    """Pull from remote (merge/rebase behavior follows repo config).

    Recovery: On conflict, same as merge — resolve files then commit.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "pulled"}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _pull_changes(repo_path, remote_name, pull_branch)
    except Exception as e:
        logger.exception("git_pull_changes failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_fetch_updates(
    repo_path: str,
    remote_name: str = "origin",
) -> dict[str, Any]:
    """Fetch remote refs without merging (safe, read-only on working tree).

    Idempotency: Safe to retry; updates remote-tracking branches.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "fetched"}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _fetch_updates(repo_path, remote_name)
    except Exception as e:
        logger.exception("git_fetch_updates failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_list_remotes(repo_path: str) -> dict[str, Any]:
    """List configured remotes and URLs.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"remotes": [{"name": str, "urls": list[str]}, ...]}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _list_remotes(repo_path)
    except Exception as e:
        logger.exception("git_list_remotes failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_add_remote(
    repo_path: str,
    remote_name: str,
    remote_url: str,
) -> dict[str, Any]:
    """Add a named remote.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"remote": str}
    """
    if not repo_path or not remote_url:
        return _clarification_response(
            "params", "repo_path, remote_name, and remote_url are required", []
        )
    try:
        return await _add_remote(repo_path, remote_name, remote_url)
    except Exception as e:
        logger.exception("git_add_remote failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_remove_remote(repo_path: str, remote_name: str) -> dict[str, Any]:
    """Remove a remote.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "removed"}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _remove_remote(repo_path, remote_name)
    except Exception as e:
        logger.exception("git_remove_remote failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_stash_changes(
    repo_path: str,
    stash_message: str | None = None,
) -> dict[str, Any]:
    """Stash working tree changes (optionally with a message).

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "stashed"}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _stash_changes(repo_path, stash_message)
    except Exception as e:
        logger.exception("git_stash_changes failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_apply_stash(repo_path: str, stash_index: int = 0) -> dict[str, Any]:
    """Apply a stash by index (0 = newest in git stash list).

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "applied"}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _apply_stash(repo_path, stash_index)
    except Exception as e:
        logger.exception("git_apply_stash failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_list_stashes(repo_path: str) -> dict[str, Any]:
    """List stash entries (raw lines from git stash list).

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"stashes": list[str]}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _list_stashes(repo_path)
    except Exception as e:
        logger.exception("git_list_stashes failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_resolve_conflicts(repo_path: str) -> dict[str, Any]:
    """List paths still in conflict (unmerged) after a failed merge/rebase.

    Recovery: Edit files to remove conflict markers, then commit.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"conflicted": list[str]}
    """
    if not repo_path:
        return _clarification_response("repo_path", "repo_path is required", [])
    try:
        return await _resolve_conflicts(repo_path)
    except Exception as e:
        logger.exception("git_resolve_conflicts failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def git_rebase_branch(repo_path: str, source_branch: str) -> dict[str, Any]:
    """Rebase current branch onto source_branch.

    Recovery: On conflict, resolve and continue via git CLI or abort.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {"status": "rebased"}
    """
    if not repo_path or not source_branch:
        return _clarification_response(
            "params", "repo_path and source_branch are required", []
        )
    try:
        return await _rebase_branch(repo_path, source_branch)
    except Exception as e:
        logger.exception("git_rebase_branch failed")
        return _error_response(str(e), "internal_error")
