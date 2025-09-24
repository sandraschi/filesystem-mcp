"""
Unit tests for repository operations.

Tests Git repository management functionality including cloning,
status checking, branch operations, and committing changes.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from filesystem_mcp.tools.repo_operations import (
    clone_repo,
    get_repo_status,
    list_branches,
    commit_changes,
    read_repo
)


def parse_tool_result(result):
    """Parse the JSON content from a ToolResult."""
    import json
    return json.loads(result.content[0].text)


class TestCloneRepo:
    """Test the clone_repo function."""

    @pytest.mark.asyncio
    async def test_clone_repo_success(self, temp_dir):
        """Test successful repository cloning."""
        target_dir = temp_dir / "cloned_repo"

        with patch('filesystem_mcp.tools.repo_operations.git.Repo.clone_from') as mock_clone:
            # Mock the cloned repository
            mock_repo = Mock()
            mock_repo.head.is_valid.return_value = True
            mock_repo.active_branch = "main"
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.head.commit.message = "Initial commit"
            mock_repo.head.commit.author.name = "Test Author"
            mock_repo.head.commit.author.email = "test@example.com"
            mock_repo.head.commit.committed_datetime = datetime.now()
            mock_repo.head.commit.parents = []
            mock_repo.remotes = []
            mock_repo.git_dir = str(target_dir / ".git")
            mock_repo.bare = False

            mock_clone.return_value = mock_repo

            result = await clone_repo.run({
                "repo_url": "https://github.com/test/repo.git",
                "target_dir": str(target_dir)
            })

            data = parse_tool_result(result)
            assert data["success"] is True
            assert "Successfully cloned" in data["message"]
            assert data["repo_path"] == str(target_dir)
            assert data["head"]["branch"] == "main"
            assert data["head"]["commit"] == "abc123"

    @pytest.mark.asyncio
    async def test_clone_repo_directory_exists(self, temp_dir):
        """Test cloning when target directory already exists and is not empty."""
        target_dir = temp_dir / "existing_dir"
        target_dir.mkdir()
        (target_dir / "existing_file.txt").write_text("existing")

        result = await clone_repo.run({
            "repo_url": "https://github.com/test/repo.git",
            "target_dir": str(target_dir)
        })

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "not empty" in data["error"]


class TestGetRepoStatus:
    """Test the get_repo_status function."""

    @pytest.mark.asyncio
    async def test_get_repo_status_success(self, temp_repo):
        """Test successful repository status retrieval."""
        result = await get_repo_status.run({"repo_path": str(temp_repo)})
        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["repo_path"] == str(temp_repo)
        assert "is_dirty" in data
        assert "active_branch" in data
        assert "staged_changes" in data
        assert "unstaged_changes" in data
        assert "untracked_files" in data

    @pytest.mark.asyncio
    async def test_get_repo_status_nonexistent_repo(self, temp_dir):
        """Test getting status of non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await get_repo_status.run({"repo_path": str(nonexistent)})
        data = parse_tool_result(result)
        assert data["success"] is False
        assert "does not exist" in data["error"]

    @pytest.mark.asyncio
    async def test_get_repo_status_not_git_repo(self, temp_dir):
        """Test getting status of directory that's not a Git repository."""
        not_repo = temp_dir / "not_repo"
        not_repo.mkdir()
        result = await get_repo_status.run({"repo_path": str(not_repo)})
        data = parse_tool_result(result)
        assert data["success"] is False
        assert "not a valid Git repository" in data["error"]


class TestListBranches:
    """Test the list_branches function."""

    @pytest.mark.asyncio
    async def test_list_branches_success(self, temp_repo):
        """Test successful branch listing."""
        result = await list_branches.run({"repo_path": str(temp_repo)})
        data = parse_tool_result(result)
        assert data["success"] is True
        assert "branches" in data
        assert "current_branch" in data
        # Should have at least one branch (main/master)
        assert len(data["branches"]) >= 1

    @pytest.mark.asyncio
    async def test_list_branches_nonexistent_repo(self, temp_dir):
        """Test listing branches in non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await list_branches.run({"repo_path": str(nonexistent)})
        data = parse_tool_result(result)
        assert data["success"] is False
        assert "does not exist" in data["error"]


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

        result = await commit_changes.run({
            "repo_path": str(temp_repo),
            "message": "Test commit",
            "add_all": False
        })

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "committed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_commit_changes_no_changes(self, temp_repo):
        """Test committing when there are no changes."""
        result = await commit_changes.run({
            "repo_path": str(temp_repo),
            "message": "Empty commit"
        })

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "no changes" in data["error"].lower()
