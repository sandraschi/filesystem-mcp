import logging
import os
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
async def repo_ops(
    operation: Literal[
        "clone_repo",
        "get_repo_status",
        "commit_changes",
        "read_repo",
        "get_repo_info",
        "get_commit_history",
        "show_commit",
        "diff_changes",
        "blame_file",
        "get_file_history",
        "revert_commit",
        "reset_to_commit",
        "cherry_pick",
    ],
    repo_path: Optional[str] = None,
    repo_url: Optional[str] = None,
    target_dir: Optional[str] = None,
    message: Optional[str] = None,
    add_all: bool = False,
    paths: Optional[list[str]] = None,
    amend: bool = False,
    max_commits: int = 50,
    since: Optional[str] = None,
    until: Optional[str] = None,
    author: Optional[str] = None,
    commit1: Optional[str] = None,
    commit2: Optional[str] = None,
    file_path: Optional[str] = None,
    include_untracked: bool = True,
    include_ignored: bool = False,
    max_depth: int = 3,
    include_files: bool = True,
    include_dirs: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Git Repository Core operations (Status, Commits, History).

    Args:
        operation (Literal, required): Available core operations:
            - "clone_repo": Clone repository (requires: repo_url, target_dir)
            - "get_repo_status": Staged/unstaged status (requires: repo_path)
            - "commit_changes": Commit changes (requires: repo_path, message)
            - "read_repo": Structure and contents (requires: repo_path)
            - "get_repo_info": General metadata (requires: repo_path)
            - "get_commit_history": Log of commits (requires: repo_path)
            - "show_commit": Detail for one commit (requires: repo_path, commit1 as hash)
            - "diff_changes": Show differences (requires: repo_path)
            - "blame_file": Line-by-line modification info (requires: repo_path, file_path)
            - "get_file_history": History for specific file (requires: repo_path, file_path)
            - "revert_commit": Undo a commit (requires: repo_path, commit1 as hash)
            - "reset_to_commit": Move HEAD to hash (requires: repo_path, commit1 as hash)
            - "cherry_pick": Apply hash to current (requires: repo_path, commit1 as hash)

        --- REPOSITORY PATHS ---

        repo_path (str | None): Path to local Git repo
        repo_url (str | None): URL for cloning
        target_dir (str | None): Local destination for clone

        --- COMMIT & HISTORY ---

        message (str | None): Commit message
        add_all (bool): Stage all changes. Default: False
        paths (List | None): Specific files to stage/commit
        amend (bool): Modify last commit. Default: False
        max_commits (int): Max history entries. Default: 50
        since/until (str | None): Date filters
        author (str | None): Author filter

        --- DIFF & BLAME ---

        commit1/commit2 (str | None): Git hashes/refs for diff/reset
        file_path (str | None): Target file for blame/history

        --- OPTIONS ---

        include_untracked/ignored (bool): Status visibility
        max_depth (int): Tree depth for reading. Default: 3
        include_files/dirs (bool): Reading filters
        force (bool): Forced reset. Default: False
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["get_repo_status", "commit_changes"]
            )

        if (
            operation
            in [
                "get_repo_status",
                "commit_changes",
                "read_repo",
                "get_repo_info",
                "get_commit_history",
                "show_commit",
                "diff_changes",
                "blame_file",
                "get_file_history",
                "revert_commit",
                "reset_to_commit",
                "cherry_pick",
            ]
            and not repo_path
        ):
            return _clarification_response("repo_path", f"repo_path is required for {operation}")

        _get_git()
        if operation == "clone_repo":
            if not repo_url:
                return _clarification_response("repo_url", "repo_url is required for clone_repo")
            if not target_dir:
                return _clarification_response("target_dir", "target_dir is required for clone_repo")
            return await _clone_repo(repo_url, target_dir)
        elif operation == "get_repo_status":
            return await _get_repo_status(repo_path, include_untracked, include_ignored)
        elif operation == "commit_changes":
            if not message and not amend:
                return _clarification_response("message", "Commit message is required (unless amending)")
            return await _commit_changes(repo_path, message, add_all, paths, amend)
        elif operation == "read_repo":
            return await _read_repo(repo_path, max_depth, include_files, include_dirs)
        elif operation == "get_repo_info":
            return await _get_repo_info(repo_path)
        elif operation == "get_commit_history":
            return await _get_commit_history(repo_path, max_commits, since, until, author, file_path)
        elif operation == "show_commit":
            if not commit1:
                return _clarification_response("commit1", "commit1 hash is required for show_commit")
            return await _show_commit(repo_path, commit1)
        elif operation == "diff_changes":
            return await _diff_changes(repo_path, commit1, commit2, file_path)
        elif operation == "blame_file":
            if not file_path:
                return _clarification_response("file_path", "file_path is required for blame_file")
            return await _blame_file(repo_path, file_path)
        elif operation == "get_file_history":
            if not file_path:
                return _clarification_response("file_path", "file_path is required for get_file_history")
            return await _get_file_history(repo_path, file_path, max_commits)
        elif operation == "revert_commit":
            if not commit1:
                return _clarification_response("commit1", "commit1 hash is required for revert_commit")
            return await _revert_commit(repo_path, commit1)
        elif operation == "reset_to_commit":
            if not commit1:
                return _clarification_response("commit1", "commit1 hash is required for reset_to_commit")
            return await _reset_to_commit(repo_path, commit1, force)
        elif operation == "cherry_pick":
            if not commit1:
                return _clarification_response("commit1", "commit1 hash is required for cherry_pick")
            return await _cherry_pick(repo_path, commit1)
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Repository operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _clone_repo(repo_url, target_dir):
    try:
        repo = git.Repo.clone_from(repo_url, target_dir)
        return _success_response(
            {"repo_path": target_dir, "active_branch": repo.active_branch.name},
            next_steps=["repo_ops(operation='get_repo_status', repo_path='...')"],
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _get_repo_status(repo_path, include_untracked, include_ignored):
    try:
        repo = git.Repo(repo_path)
        status = repo.git.status(porcelain=True, untracked_files="all" if include_untracked else "no")
        staged, unstaged, untracked = [], [], []
        for line in status.split("\n"):
            if not line.strip():
                continue
            code, fname = line[:2], line[3:]
            if code[0] in "AMDRCU":
                staged.append({"status": code[0], "file": fname})
            if code[1] in "MDRCU?":
                if code[1] == "?":
                    untracked.append(fname)
                else:
                    unstaged.append({"status": code[1], "file": fname})
        return _success_response(
            {
                "repo_path": repo_path,
                "is_dirty": repo.is_dirty(),
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
            },
            next_steps=[
                "repo_ops(operation='commit_changes', message='...')",
                "repo_ops(operation='diff_changes')",
            ],
            related_ops=["get_repo_info", "git_ops(operation='list_branches')"],
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _commit_changes(repo_path, message, add_all, paths, amend):
    try:
        repo = git.Repo(repo_path)
        if add_all:
            repo.git.add(all=True)
        elif paths:
            repo.index.add(paths)
        commit = repo.index.commit(message, amend=amend)
        return _success_response(
            {"commit_hash": commit.hexsha, "author": commit.author.name},
            next_steps=["git_ops(operation='push_changes')"],
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _read_repo(repo_path, max_depth, include_files, include_dirs):
    try:
        repo = git.Repo(repo_path)

        def get_tree(tree, path="", depth=0):
            if depth > max_depth:
                return None
            struct = {"name": os.path.basename(path) or ".", "type": "tree", "children": []}
            for item in tree:
                if item.type == "blob" and include_files:
                    struct["children"].append({"name": item.name, "type": "blob", "size": item.size})
                elif item.type == "tree" and include_dirs:
                    sub = get_tree(item, os.path.join(path, item.name), depth + 1)
                    if sub:
                        struct["children"].append(sub)
            return struct

        return _success_response({"structure": get_tree(repo.head.commit.tree)})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _get_repo_info(repo_path):
    try:
        repo = git.Repo(repo_path)
        return _success_response(
            {
                "repo_path": repo_path,
                "active_branch": repo.active_branch.name,
                "head_commit": repo.head.commit.hexsha,
                "is_dirty": repo.is_dirty(),
                "remotes": [r.name for r in repo.remotes],
            }
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _get_commit_history(repo_path, max_commits, since, until, author, file_path):
    try:
        repo = git.Repo(repo_path)
        commits = list(repo.iter_commits(max_count=max_commits, paths=file_path))
        return _success_response(
            {
                "commits": [
                    {
                        "hash": c.hexsha,
                        "message": c.message.strip(),
                        "author": c.author.name,
                        "date": c.committed_datetime.isoformat(),
                    }
                    for c in commits
                ],
            }
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _show_commit(repo_path, commit_hash):
    try:
        repo = git.Repo(repo_path)
        c = repo.commit(commit_hash)
        return _success_response(
            {
                "commit": {
                    "hash": c.hexsha,
                    "message": c.message.strip(),
                    "author": c.author.name,
                    "date": c.committed_datetime.isoformat(),
                },
            }
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _diff_changes(repo_path, commit1, commit2, file_path):
    try:
        repo = git.Repo(repo_path)
        if commit1 and commit2:
            diff = repo.git.diff(commit1, commit2, file_path or "--")
        elif commit1:
            diff = repo.git.diff(commit1, file_path or "--")
        else:
            diff = repo.git.diff(file_path or "--")
        return _success_response({"diff": diff})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _blame_file(repo_path, file_path):
    try:
        repo = git.Repo(repo_path)
        blame = repo.blame("HEAD", file_path)
        return _success_response(
            {
                "blame": [
                    {"author": c.author.name, "date": c.committed_datetime.isoformat()}
                    for c, lines in blame
                ],
            }
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _get_file_history(repo_path, file_path, max_commits):
    try:
        repo = git.Repo(repo_path)
        commits = list(repo.iter_commits(paths=file_path, max_count=max_commits))
        return _success_response(
            {"history": [{"hash": c.hexsha, "message": c.message.strip()} for c in commits]}
        )
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _revert_commit(repo_path, commit_hash):
    try:
        git.Repo(repo_path).git.revert(commit_hash, no_edit=True)
        return _success_response({"reverted": commit_hash})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _reset_to_commit(repo_path, commit_hash, hard):
    try:
        git.Repo(repo_path).git.reset("--hard" if hard else "--soft", commit_hash)
        return _success_response({"reset_to": commit_hash})
    except Exception as e:
        return _error_response(str(e), "git_error")


async def _cherry_pick(repo_path, commit_hash):
    try:
        git.Repo(repo_path).git.cherry_pick(commit_hash)
        return _success_response({"cherry_picked": commit_hash})
    except Exception as e:
        return _error_response(str(e), "git_error")
