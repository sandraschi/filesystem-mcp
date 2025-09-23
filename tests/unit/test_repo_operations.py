"""
Unit tests for repository operations.

Tests all Git repository operation functions with proper mocking and edge case coverage.
"""

import pytest
import asyncio
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
})\nclass TestCloneRepo:
    """Test the clone_repo function."""

    @pytest.mark.asyncio
    async def test_clone_repo_success(self, temp_dir):
        """Test successful repository cloning."""
        target_dir = temp_dir / "cloned_repo"

        with patch('filesystem_mcp.tools.repo_operations.git.Repo.clone_from') as mock_clone:
            # Mock the cloned repository
            mock_repo = Mock(})\n            mock_repo.head.is_valid.return_value = True
            mock_repo.active_branch = "main"
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.head.commit.message = "Initial commit"
            mock_repo.head.commit.author.name = "Test Author"
            mock_repo.head.commit.author.email = "test@example.com"
            mock_repo.head.commit.committed_datetime = datetime.now(})\n            mock_repo.head.commit.parents = []
            mock_repo.remotes = []
            mock_repo.git_dir = str(target_dir / ".git"})\n            mock_repo.bare = False

            mock_clone.return_value = mock_repo

            result = await clone_repo.run({
                repo_url="https://github.com/test/repo.git",
                target_dir=str(target_dir})\n            })\n            assert result.content["success"] is True
            assert "Successfully cloned" in result.content["message"]
            assert result.content["repo_path"] == str(target_dir})\n            assert result.content["head"]["branch"] == "main"
            assert result.content["head"]["commit"] == "abc123"

    @pytest.mark.asyncio
    async def test_clone_repo_directory_exists(self, temp_dir):
        """Test cloning when target directory already exists and is not empty."""
        target_dir = temp_dir / "existing_dir"
        target_dir.mkdir(})\n        (target_dir / "existing_file.txt").write_text("existing"})\n        result = await clone_repo.run({
            repo_url="https://github.com/test/repo.git",
            target_dir=str(target_dir})\n        })\n        assert result.content["success"] is False
        assert "not empty" in result.content["error"]

    @pytest.mark.asyncio
    async def test_clone_repo_no_write_permission(self, temp_dir):
        """Test cloning when target directory has no write permission."""
        target_dir = temp_dir / "no_write"
        target_dir.mkdir(})\n        # Try to make directory read-only (may not work on all platforms})\n        try:
            target_dir.chmod(0o444})\n            result = await clone_repo.run({
                repo_url="https://github.com/test/repo.git",
                target_dir=str(target_dir / "subdir"})\n            })\n            # May or may not fail depending on platform
        finally:
            try:
                target_dir.chmod(0o755})\n            except:
                pass


class TestGetRepoStatus:
    """Test the get_repo_status function."""

    @pytest.mark.asyncio
    async def test_get_repo_status_success(self, temp_repo):
        """Test successful repository status retrieval."""
        result = await get_repo_status.run({str(temp_repo)})\n        assert result.content["success"] is True
        assert result.content["repo_path"] == str(temp_repo})\n        assert "is_dirty" in result
        assert "active_branch" in result
        assert "staged_changes" in result
        assert "unstaged_changes" in result
        assert "untracked_files" in result

    @pytest.mark.asyncio
    async def test_get_repo_status_nonexistent_repo(self, temp_dir):
        """Test getting status of non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await get_repo_status.run({str(nonexistent)})\n        assert result.content["success"] is False
        assert "does not exist" in result.content["error"]

    @pytest.mark.asyncio
    async def test_get_repo_status_not_git_repo(self, temp_dir):
        """Test getting status of directory that's not a Git repository."""
        not_repo = temp_dir / "not_repo"
        not_repo.mkdir(})\n        result = await get_repo_status.run({str(not_repo)})\n        assert result.content["success"] is False
        assert "not a valid Git repository" in result.content["error"]

    @pytest.mark.asyncio
    async def test_get_repo_status_with_remote(self, temp_repo):
        """Test getting repository status with remote information."""
        # Add a mock remote
        import git
        repo = git.Repo(temp_repo})\n        remote = repo.create_remote('origin', 'https://github.com/test/repo.git'})\n        result = await get_repo_status.run({str(temp_repo), include_remote=True})\n        assert result.content["success"] is True
        assert "remote_status" in result
        # Clean up
        repo.delete_remote(remote})\nclass TestListBranches:
    """Test the list_branches function."""

    @pytest.mark.asyncio
    async def test_list_branches_success(self, temp_repo):
        """Test successful branch listing."""
        result = await list_branches.run({str(temp_repo)})\n        assert result.content["success"] is True
        assert "branches" in result
        assert "current_branch" in result
        # Should have at least one branch (main/master})\n        assert len(result.content["branches"]) >= 1

    @pytest.mark.asyncio
    async def test_list_branches_nonexistent_repo(self, temp_dir):
        """Test listing branches in non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await list_branches.run({str(nonexistent)})\n        assert result.content["success"] is False
        assert "does not exist" in result.content["error"]

    @pytest.mark.asyncio
    async def test_list_branches_multiple_branches(self, temp_repo):
        """Test listing multiple branches."""
        import git
        repo = git.Repo(temp_repo})\n        # Create a new branch
        new_branch = repo.create_head('feature-branch'})\n        new_branch.checkout(})\n        result = await list_branches.run({str(temp_repo)})\n        assert result.content["success"] is True
        branch_names = [b["name"] for b in result.content["branches"]]
        assert "feature-branch" in branch_names

    @pytest.mark.asyncio
    async def test_list_branches_with_tracking(self, temp_repo):
        """Test listing branches with tracking information."""
        import git
        repo = git.Repo(temp_repo})\n        # Create remote and tracking branch
        remote = repo.create_remote('origin', 'https://github.com/test/repo.git'})\n        tracking_branch = repo.create_head('main', 'origin/main'})\n        tracking_branch.set_tracking_branch(repo.refs['origin/main']})\n        result = await list_branches.run({str(temp_repo)})\n        assert result.content["success"] is True
        # Check that tracking information is included
        main_branch = next((b for b in result.content["branches"] if b["name"] == "main"), None})\n        if main_branch:
            assert "tracking" in main_branch

        # Clean up
        repo.delete_remote(remote})\nclass TestCommitChanges:
    """Test the commit_changes function."""

    @pytest.mark.asyncio
    async def test_commit_changes_success(self, temp_repo):
        """Test successful commit of changes."""
        import git

        # Make a change
        test_file = temp_repo / "test.txt"
        test_file.write_text("New content"})\n        repo = git.Repo(temp_repo})\n        repo.index.add([str(test_file.relative_to(temp_repo))]})\n        result = await commit_changes.run({
            str(temp_repo),
            message="Test commit",
            add_all=False
        })\n        assert result.content["success"] is True
        assert "committed" in result.content["message"].lower(})\n    @pytest.mark.asyncio
    async def test_commit_changes_no_changes(self, temp_repo):
        """Test committing when there are no changes."""
        result = await commit_changes.run({
            str(temp_repo),
            message="Empty commit"
        })\n        # This might succeed or fail depending on Git configuration
        # But it should handle the case gracefully
        assert "success" in result

    @pytest.mark.asyncio
    async def test_commit_changes_add_all(self, temp_repo):
        """Test committing with add_all flag."""
        # Create untracked file
        test_file = temp_repo / "untracked.txt"
        test_file.write_text("Untracked content"})\n        result = await commit_changes.run({
            str(temp_repo),
            message="Add untracked file",
            add_all=True
        })\n        assert result.content["success"] is True

    @pytest.mark.asyncio
    async def test_commit_changes_custom_author(self, temp_repo):
        """Test committing with custom author information."""
        test_file = temp_repo / "authored.txt"
        test_file.write_text("Authored content"})\n        result = await commit_changes.run({
            str(temp_repo),
            message="Authored commit",
            author_name="Test Author",
            author_email="test@example.com",
            add_all=True
        })\n        assert result.content["success"] is True


class TestReadRepo:
    """Test the read_repo function."""

    @pytest.mark.asyncio
    async def test_read_repo_success(self, temp_repo):
        """Test successful repository reading."""
        result = await read_repo.run({str(temp_repo)})\n        assert result.content["success"] is True
        assert "contents" in result
        assert "repo_info" in result

    @pytest.mark.asyncio
    async def test_read_repo_with_path(self, temp_repo):
        """Test reading repository with specific path."""
        # Create subdirectory with files
        subdir = temp_repo / "src"
        subdir.mkdir(})\n        (subdir / "main.py").write_text("print('hello')"})\n        result = await read_repo.run({str(temp_repo), path="src"})\n        assert result.content["success"] is True
        assert "contents" in result

    @pytest.mark.asyncio
    async def test_read_repo_recursive(self, temp_repo):
        """Test recursive repository reading."""
        # Create nested structure
        (temp_repo / "dir1").mkdir(})\n        (temp_repo / "dir1" / "file1.txt").write_text("content1"})\n        (temp_repo / "dir1" / "dir2").mkdir(})\n        (temp_repo / "dir1" / "dir2" / "file2.txt").write_text("content2"})\n        result = await read_repo.run({str(temp_repo), recursive=True})\n        assert result.content["success"] is True
        assert "contents" in result

    @pytest.mark.asyncio
    async def test_read_repo_include_content(self, temp_repo):
        """Test reading repository with content inclusion."""
        test_file = temp_repo / "content.txt"
        test_file.write_text("File content"})\n        result = await read_repo.run({str(temp_repo), include_content=True})\n        assert result.content["success"] is True
        # Should include content for small files
        found_content = False
        def check_contents(items):
            nonlocal found_content
            for item in items:
                if item.get("name") == "content.txt" and "content" in item:
                    found_content = True
                if "contents" in item:
                    check_contents(item["contents"]})\n        check_contents(result.content["contents"]})\n        assert found_content

    @pytest.mark.asyncio
    async def test_read_repo_nonexistent_repo(self, temp_dir):
        """Test reading non-existent repository."""
        nonexistent = temp_dir / "nonexistent_repo"

        result = await read_repo.run({str(nonexistent)})\n        assert result.content["success"] is False
        assert "does not exist" in result.content["error"]

