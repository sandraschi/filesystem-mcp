import logging
from typing import Any, Literal, Optional

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _success_response,
)

logger = logging.getLogger(__name__)

# Git library will be imported when needed
git = None


def _get_git():
    global git
    if git is None:
        try:
            import git
        except ImportError as e:
            raise RuntimeError(
                "Git operations require 'GitPython'. Install with: pip install GitPython"
            ) from e
    return git


@_get_app().tool()
async def git_ops(
    operation: Literal[
        "create_branch",
        "switch_branch",
        "merge_branch",
        "delete_branch",
        "list_branches",
        "create_tag",
        "list_tags",
        "delete_tag",
        "push_changes",
        "pull_changes",
        "fetch_updates",
        "list_remotes",
        "add_remote",
        "remove_remote",
        "stash_changes",
        "apply_stash",
        "list_stashes",
        "resolve_conflicts",
        "rebase_branch",
    ],
    repo_path: Optional[str] = None,
    branch_name: Optional[str] = None,
    tag_name: Optional[str] = None,
    tag_message: Optional[str] = None,
    source_branch: Optional[str] = None,
    target_branch: Optional[str] = None,
    remote_name: str = "origin",
    remote_url: Optional[str] = None,
    push_branch: Optional[str] = None,
    pull_branch: Optional[str] = None,
    stash_message: Optional[str] = None,
    stash_index: int = 0,
    force: bool = False,
) -> dict[str, Any]:
    """Git Administrative operations (Branches, Tags, Remotes, Stash).

    Args:
        operation (Literal, required): Available management operations:
            - "create_branch": New branch (requires: repo_path, branch_name)
            - "switch_branch": Checkout branch (requires: repo_path, branch_name)
            - "merge_branch": Combine branches (requires: repo_path, source_branch)
            - "delete_branch": Remove branch (requires: repo_path, branch_name)
            - "list_branches": Show local/remote branches (requires: repo_path)
            - "create_tag": New tag (requires: repo_path, tag_name)
            - "list_tags": Show tags (requires: repo_path)
            - "delete_tag": Remove tag (requires: repo_path, tag_name)
            - "push_changes": Upload to remote (requires: repo_path)
            - "pull_changes": Download from remote (requires: repo_path)
            - "fetch_updates": Sync metadata (requires: repo_path)
            - "list_remotes": Show remotes (requires: repo_path)
            - "add_remote": New remote (requires: repo_path, remote_name, remote_url)
            - "remove_remote": Delete remote (requires: repo_path, remote_name)
            - "stash_changes": Save WIP (requires: repo_path)
            - "apply_stash": Restore WIP (requires: repo_path)
            - "list_stashes": Show WIP list (requires: repo_path)
            - "resolve_conflicts": List unmerged (requires: repo_path)
            - "rebase_branch": Rebase current (requires: repo_path, source_branch)

        --- REPOSITORY PATHS ---

        repo_path (str | None): Path to local Git repo

        --- BRANCH & TAG ---

        branch_name (str | None): Target branch name
        tag_name (str | None): Target tag name
        tag_message (str | None): Tag annotation
        source_branch (str | None): Branch to merge/rebase FROM
        target_branch (str | None): Branch to merge INTO

        --- REMOTES ---

        remote_name (str): Remote identifier. Default: "origin"
        remote_url (str | None): Remote URL for adding
        push_branch/pull_branch (str | None): Specific branches for sync

        --- STASH ---

        stash_message (str | None): WIP description
        stash_index (int): WIP list position. Default: 0

        --- OPTIONS ---

        force (bool): Force delete/push. Default: False
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["list_branches", "create_branch"]
            )

        if not repo_path:
            return _clarification_response("repo_path", f"repo_path is required for {operation}")

        _get_git()
        if operation == "create_branch":
            if not branch_name:
                return _clarification_response(
                    "branch_name", "branch_name is required for create_branch"
                )
            return await _create_branch(repo_path, branch_name)
        elif operation == "switch_branch":
            if not branch_name:
                return _clarification_response(
                    "branch_name", "branch_name is required for switch_branch"
                )
            return await _switch_branch(repo_path, branch_name)
        elif operation == "merge_branch":
            if not source_branch:
                return _clarification_response(
                    "source_branch", "source_branch is required for merge_branch"
                )
            return await _merge_branch(repo_path, source_branch, target_branch)
        elif operation == "delete_branch":
            if not branch_name:
                return _clarification_response(
                    "branch_name", "branch_name is required for delete_branch"
                )
            return await _delete_branch(repo_path, branch_name, force)
        elif operation == "list_branches":
            return await _list_branches(repo_path)
        elif operation == "create_tag":
            if not tag_name:
                return _clarification_response("tag_name", "tag_name is required for create_tag")
            return await _create_tag(repo_path, tag_name, tag_message)
        elif operation == "list_tags":
            return await _list_tags(repo_path)
        elif operation == "delete_tag":
            if not tag_name:
                return _clarification_response("tag_name", "tag_name is required for delete_tag")
            return await _delete_tag(repo_path, tag_name)
        elif operation == "push_changes":
            return await _push_changes(repo_path, remote_name, push_branch, force)
        elif operation == "pull_changes":
            return await _pull_changes(repo_path, remote_name, pull_branch)
        elif operation == "fetch_updates":
            return await _fetch_updates(repo_path, remote_name)
        elif operation == "list_remotes":
            return await _list_remotes(repo_path)
        elif operation == "add_remote":
            if not remote_url:
                return _clarification_response("remote_url", "remote_url is required for add_remote")
            return await _add_remote(repo_path, remote_name, remote_url)
        elif operation == "remove_remote":
            return await _remove_remote(repo_path, remote_name)
        elif operation == "stash_changes":
            return await _stash_changes(repo_path, stash_message)
        elif operation == "apply_stash":
            return await _apply_stash(repo_path, stash_index)
        elif operation == "list_stashes":
            return await _list_stashes(repo_path)
        elif operation == "resolve_conflicts":
            return await _resolve_conflicts(repo_path)
        elif operation == "rebase_branch":
            if not source_branch:
                return _clarification_response(
                    "source_branch", "source_branch is required for rebase_branch"
                )
            return await _rebase_branch(repo_path, source_branch)
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Git management operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _create_branch(repo_path, branch_name):
    try:
        repo = git.Repo(repo_path)
        repo.create_head(branch_name)
        return _success_response(
            {"branch": branch_name}, next_steps=[f"git_ops(operation='switch_branch', branch_name='{branch_name}')"]
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _switch_branch(repo_path, branch_name):
    try:
        git.Repo(repo_path).git.checkout(branch_name)
        return _success_response({"switched_to": branch_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _merge_branch(repo_path, source, target):
    try:
        repo = git.Repo(repo_path)
        if target:
            repo.git.checkout(target)
        repo.git.merge(source)
        return _success_response({"merged": source})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _delete_branch(repo_path, branch_name, force):
    try:
        repo = git.Repo(repo_path)
        repo.git.branch("-D" if force else "-d", branch_name)
        return _success_response({"deleted": branch_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_branches(repo_path):
    try:
        repo = git.Repo(repo_path)
        return _success_response(
            {
                "local": [b.name for b in repo.branches],
                "active": repo.active_branch.name,
            },
            next_steps=[
                "git_ops(operation='switch_branch', branch_name='...')",
                "git_ops(operation='merge_branch')",
            ],
            related_operations=["list_tags", "list_remotes"],
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _create_tag(repo_path, tag_name, message):
    try:
        repo = git.Repo(repo_path)
        repo.create_tag(tag_name, message=message)
        return _success_response({"tag": tag_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_tags(repo_path):
    try:
        return _success_response({"tags": [t.name for t in git.Repo(repo_path).tags]})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _delete_tag(repo_path, tag_name):
    try:
        git.Repo(repo_path).delete_tag(tag_name)
        return _success_response({"deleted": tag_name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _push_changes(repo_path, remote, branch, force):
    try:
        r = git.Repo(repo_path).remote(remote)
        r.push(branch, force=force) if branch else r.push(force=force)
        return _success_response({"status": "pushed"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _pull_changes(repo_path, remote, branch):
    try:
        r = git.Repo(repo_path).remote(remote)
        r.pull(branch) if branch else r.pull()
        return _success_response({"status": "pulled"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _fetch_updates(repo_path, remote):
    try:
        git.Repo(repo_path).remote(remote).fetch()
        return _success_response({"status": "fetched"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_remotes(repo_path):
    try:
        return _success_response(
            {
                "remotes": [
                    {"name": r.name, "urls": list(r.urls)} for r in git.Repo(repo_path).remotes
                ],
            }
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _add_remote(repo_path, name, url):
    try:
        git.Repo(repo_path).create_remote(name, url)
        return _success_response({"remote": name})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _remove_remote(repo_path, name):
    try:
        git.Repo(repo_path).delete_remote(name)
        return _success_response({"status": "removed"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _stash_changes(repo_path, message):
    try:
        git.Repo(repo_path).git.stash("push", "-m", message) if message else git.Repo(
            repo_path
        ).git.stash("push")
        return _success_response({"status": "stashed"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _apply_stash(repo_path, index):
    try:
        git.Repo(repo_path).git.stash("apply", f"stash@{{{index}}}")
        return _success_response({"status": "applied"})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _list_stashes(repo_path):
    try:
        stashes = git.Repo(repo_path).git.stash("list").split("\n")
        return _success_response({"stashes": stashes})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _resolve_conflicts(repo_path):
    try:
        unmerged = git.Repo(repo_path).git.diff("--name-only", "--diff-filter=U").split("\n")
        return _success_response({"conflicted": [u for u in unmerged if u.strip()]})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _rebase_branch(repo_path, source):
    try:
        git.Repo(repo_path).git.rebase(source)
        return _success_response({"status": "rebased"})
    except Exception as e:
        return _error_response(str(e), "git_error")
