"""
Unit tests for repository operations.

Tests Git repository management functionality including cloning,
status checking, branch operations, and committing changes.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from filesystem_mcp.tools.portmanteau_git_mgmt import git_list_branches
from filesystem_mcp.tools.portmanteau_repository import repo_ops


def parse_tool_result(result):
    """Parse tool output supporting dict and ToolResult styles."""
    import json

    if isinstance(result, dict):
        return result
    return json.loads(result.content[0].text)


class _RepoToolAdapter:
    """Expose legacy .run(payload) style on top of repo_ops."""

    def __init__(self, operation: str):
        self.operation = operation

    async def run(self, payload: dict):
        merged = {"operation": self.operation}
        merged.update(payload)
        return await repo_ops(**merged)


class _SimpleToolAdapter:
    """Expose legacy .run(payload) style for direct tools."""

    def __init__(self, fn):
        self.fn = fn

    async def run(self, payload: dict):
        return await self.fn(**payload)


clone_repo = _RepoToolAdapter("clone_repo")
commit_changes = _RepoToolAdapter("commit_changes")
get_repo_status = _RepoToolAdapter("get_repo_status")
list_branches = _SimpleToolAdapter(git_list_branches)


class TestCloneRepo:
    """Test the clone_repo function."""

    @pytest.mark.asyncio
    async def test_clone_repo_success(self, temp_dir):
        """Test successful repository cloning."""
        target_dir = temp_dir / "cloned_repo"

        with (
            patch("filesystem_mcp.tools.portmanteau_repository._get_git") as mock_get_git,
            patch("filesystem_mcp.tools.portmanteau_repository.git") as mock_git_global,
        ):
            # Mock the cloned repository
            mock_repo = Mock()
            mock_repo.head.is_valid.return_value = True
            mock_repo.active_branch = Mock()
            mock_repo.active_branch.name = "main"
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.head.commit.message = "Initial commit"
            mock_repo.head.commit.author.name = "Test Author"
            mock_repo.head.commit.author.email = "test@example.com"
            mock_repo.head.commit.committed_datetime = datetime.now()
            mock_repo.head.commit.parents = []
            mock_repo.remotes = []
            mock_repo.git_dir = str(target_dir / ".git")
            mock_repo.bare = False

            mock_git_mod = Mock()
            mock_git_mod.Repo.clone_from.return_value = mock_repo
            mock_get_git.return_value = mock_git_mod
            mock_git_global.Repo.clone_from.return_value = mock_repo

            result = await clone_repo.run(
                {"repo_url": "https://github.com/test/repo.git", "target_dir": str(target_dir)}
            )

            data = parse_tool_result(result)
            assert data["success"] is True
            assert data["result"]["repo_path"] == str(target_dir)
            assert data["result"]["active_branch"] == "main"

    @pytest.mark.asyncio
    async def test_clone_repo_directory_exists(self, temp_dir):
        """Test cloning when target directory already exists and is not empty."""
        target_dir = temp_dir / "existing_dir"
        target_dir.mkdir()
        (target_dir / "existing_file.txt").write_text("existing")

        result = await clone_repo.run(
            {"repo_url": "https://github.com/test/repo.git", "target_dir": str(target_dir)}
        )

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "not empty" in data["error"].lower() or "already exists" in data["error"].lower()


class TestGetRepoStatus:
    """Test the get_repo_status function."""

    @pytest.mark.asyncio
    async def test_get_repo_status_success(self, temp_repo):
        """Test successful repository status retrieval."""
        result = await get_repo_status.run({"repo_path": str(temp_repo)})
        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["repo_path"] == str(temp_repo)
        assert "is_dirty" in data["result"]
        assert "staged" in data["result"]
        assert "unstaged" in data["result"]
        assert "untracked" in data["result"]

    @pytest.mark.asyncio
    async def test_get_repo_status_nonexistent_repo(self, temp_dir):
        """Test getting status of non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await get_repo_status.run({"repo_path": str(nonexistent)})
        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_get_repo_status_not_git_repo(self, temp_dir):
        """Test getting status of directory that's not a Git repository."""
        not_repo = temp_dir / "not_repo"
        not_repo.mkdir()
        result = await get_repo_status.run({"repo_path": str(not_repo)})
        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data


class TestListBranches:
    """Test the list_branches function."""

    @pytest.mark.asyncio
    async def test_list_branches_success(self, temp_repo):
        """Test successful branch listing."""
        result = await list_branches.run({"repo_path": str(temp_repo)})
        data = parse_tool_result(result)
        assert data["success"] is True
        assert "local" in data["result"]
        assert "active" in data["result"]
        # Should have at least one branch (main/master)
        assert len(data["result"]["local"]) >= 1

    @pytest.mark.asyncio
    async def test_list_branches_nonexistent_repo(self, temp_dir):
        """Test listing branches in non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await list_branches.run({"repo_path": str(nonexistent)})
        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data


class TestCommitChanges:
    """Test the commit_changes function."""

    @pytest.mark.asyncio
    async def test_commit_changes_success(self, temp_repo):
        """Test successful commit of changes."""
        import git

        # Make a change
        test_file = temp_repo / "test.txt"
        test_file.write_text("New content")
        repo = git.Repo(temp_repo)
        repo.index.add([str(test_file.relative_to(temp_repo))])

        result = await commit_changes.run(
            {"repo_path": str(temp_repo), "message": "Test commit", "add_all": False}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "commit_hash" in data["result"]

    @pytest.mark.asyncio
    async def test_commit_changes_no_changes(self, temp_repo):
        """Test committing when there are no changes."""
        result = await commit_changes.run({"repo_path": str(temp_repo), "message": "Empty commit"})

        data = parse_tool_result(result)
        assert data["success"] is True
