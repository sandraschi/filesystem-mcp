"""
Integration tests for complete workflow scenarios.

Tests real workflows that combine multiple tools to accomplish tasks.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from filesystem_mcp.tools.file_operations import (
    get_file_info,
    list_directory,
    read_file,
    write_file,
)
from filesystem_mcp.tools.repo_operations import clone_repo, get_repo_status
from filesystem_mcp.tools.system_tools import get_help, get_system_status


class TestProjectSetupWorkflow:
    """Test complete project setup workflow."""

    @pytest.mark.asyncio
    async def test_create_project_structure(self, temp_dir):
        """Test creating a complete project structure."""
        project_dir = temp_dir / "my_project"
        project_dir.mkdir()

        # Create main directories
        src_dir = project_dir / "src"
        tests_dir = project_dir / "tests"
        docs_dir = project_dir / "docs"

        # Write configuration files
        pyproject_content = """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
version = "0.1.0"
description = "A sample project"
"""

        readme_content = "# My Project\n\nThis is a sample project.\n"

        # Create files
        result1 = await write_file.run({"file_path": str(src_dir / "__init__.py"), "content": ""})
        result2 = await write_file.run({"file_path": str(tests_dir / "__init__.py"), "content": ""})
        result3 = await write_file.run(
            {"file_path": str(docs_dir / "README.md"), "content": "Documentation"}
        )
        result4 = await write_file.run(
            {"file_path": str(project_dir / "pyproject.toml"), "content": pyproject_content}
        )
        result5 = await write_file.run(
            {"file_path": str(project_dir / "README.md"), "content": readme_content}
        )

        # Verify all operations succeeded
        assert result1["success"] is True
        assert result2["success"] is True
        assert result3["success"] is True
        assert result4["success"] is True
        assert result5["success"] is True

        # Verify directory structure
        result = await list_directory.run({"directory_path": str(project_dir), "recursive": True})
        data = parse_tool_result(result)
        assert "files" in data

        # Check that all expected files exist
        created_files = []
        for item in data["files"]:
            if item["type"] == "file":
                created_files.append(item["name"])

        assert "pyproject.toml" in created_files
        assert "README.md" in created_files
        assert "__init__.py" in created_files

    @pytest.mark.asyncio
    async def test_project_analysis_workflow(self, temp_dir):
        """Test analyzing a project structure."""
        # Set up a sample project
        project_dir = temp_dir / "analysis_project"
        project_dir.mkdir()

        # Create various file types
        await write_file.run(
            {"file_path": str(project_dir / "main.py"), "content": "print('Hello, World!')"}
        )
        await write_file.run(
            {
                "file_path": str(project_dir / "config.json"),
                "content": '{"debug": true, "port": 8080}',
            }
        )
        await write_file.run(
            {"file_path": str(project_dir / "README.md"), "content": "# Analysis Project"}
        )
        await write_file.run(
            {"file_path": str(project_dir / ".gitignore"), "content": "*.pyc\n__pycache__/"}
        )

        # Create subdirectory
        src_dir = project_dir / "src"
        src_dir.mkdir()
        await write_file.run(
            {"file_path": str(src_dir / "utils.py"), "content": "def helper(): pass"}
        )

        # Analyze the project
        result = await list_directory.run(
            {"directory_path": str(project_dir), "recursive": True, "include_hidden": True}
        )
        data = parse_tool_result(result)
        assert "files" in data

        # Read and analyze key files
        pyproject_result = await read_file.run({"file_path": str(project_dir / "config.json")})
        pyproject_data = parse_tool_result(pyproject_result)
        assert pyproject_data["success"] is True

        config_data = json.loads(pyproject_data["content"])
        assert config_data["debug"] is True
        assert config_data["port"] == 8080

        # Check file info for main script
        main_info_result = await get_file_info.run({"file_path": str(project_dir / "main.py")})
        main_info = parse_tool_result(main_info_result)
        assert main_info["success"] is True
        assert main_info["size"] > 0
        assert main_info["is_file"] is True


class TestRepositoryWorkflow:
    """Test Git repository workflows."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.repo_operations.git.Repo.clone_from")
    async def test_repository_clone_and_analysis(self, mock_clone, temp_dir):
        """Test cloning a repository and analyzing it."""
        # Mock the repository clone
        mock_repo = Mock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.active_branch = "main"
        mock_repo.head.commit.hexsha = "abc123456789"
        mock_repo.head.commit.message = "Initial commit"
        mock_repo.head.commit.author.name = "Test Author"
        mock_repo.head.commit.author.email = "test@example.com"
        mock_repo.head.commit.committed_datetime = datetime.now()
        mock_repo.head.commit.parents = []
        mock_repo.remotes = []
        mock_repo.git_dir = str(temp_dir / "repo" / ".git")
        mock_repo.bare = False
        mock_clone.return_value = mock_repo

        # Clone repository
        clone_result = await clone_repo.run(
            {"repo_url": "https://github.com/test/repo.git", "target_dir": str(temp_dir / "repo")}
        )
        clone_data = parse_tool_result(clone_result)
        assert clone_data["success"] is True

        # Get repository status
        status_result = await get_repo_status.run({"repo_path": str(temp_dir / "repo")})
        status_data = parse_tool_result(status_result)
        assert status_data["success"] is True
        assert status_data["active_branch"] == "main"
        assert "head_commit" in status_data


class TestHelpAndStatusWorkflow:
    """Test help and status system workflows."""

    @pytest.mark.asyncio
    async def test_comprehensive_help_system(self):
        """Test the complete help system functionality."""
        # Get overview
        overview = await get_help()
        assert overview["success"] is True
        assert "data" in overview
        assert len(overview["data"]["categories"]) == 4

        # Get category help
        category_help = await get_help("file_operations")
        assert category_help["success"] is True
        assert category_help["data"]["name"] == "File Operations"

        # Get tool help
        tool_help = await get_help("file_operations", "read_file")
        assert tool_help["success"] is True
        assert tool_help["data"]["name"] == "read_file"
        assert "description" in tool_help["data"]
        assert "parameters" in tool_help["data"]

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.system_tools.psutil")
    @patch("filesystem_mcp.tools.system_tools.platform")
    async def test_system_status_integration(self, mock_platform, mock_psutil):
        """Test system status with mocked dependencies."""
        # Mock system info
        mock_platform.platform.return_value = "Linux-5.4.0-74-generic-x86_64-with-glibc2.29"
        mock_platform.processor.return_value = "x86_64"
        mock_platform.architecture.return_value = ("64bit", "ELF")

        # Mock psutil
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.cpu_percent.return_value = [45.0, 23.1, 67.8, 12.4, 89.0, 34.6, 56.7, 78.9]
        mock_psutil.virtual_memory.return_value = Mock(
            total=17179869184, available=8589934592, percent=50.0, used=8589934592, free=4294967296
        )

        # Get system status
        status = await get_system_status(include_processes=False, include_disk=False)
        assert status["success"] is True

        # Verify system information
        system_info = status["system"]
        assert "platform" in system_info
        assert "processor" in system_info

        # Verify CPU information
        cpu_info = status["cpu"]
        assert "physical_cores" in cpu_info
        assert "logical_cores" in cpu_info

        # Verify memory information
        memory_info = status["memory"]
        assert memory_info["total"] == 17179869184
        assert memory_info["available"] == 8589934592


class TestErrorHandlingWorkflow:
    """Test error handling across multiple tools."""

    @pytest.mark.asyncio
    async def test_file_operation_error_handling(self, temp_dir):
        """Test error handling in file operations."""
        # Try to read non-existent file
        result = await read_file(str(temp_dir / "nonexistent.txt"))
        assert result["success"] is False
        assert "error" in result

        # Try to write to directory without permission (if possible)
        # This might not work on all systems, so we'll skip it

        # Try to list non-existent directory
        result = await list_directory(str(temp_dir / "nonexistent_dir"))
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_repository_error_handling(self, temp_dir):
        """Test error handling in repository operations."""
        # Try to get status of non-existent repository
        result = await get_repo_status(str(temp_dir / "nonexistent_repo"))
        assert result["success"] is False
        assert "error" in result

        # Try to clone to existing non-empty directory
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()
        (existing_dir / "file.txt").write_text("content")

        result = await clone_repo(
            repo_url="https://github.com/test/repo.git", target_dir=str(existing_dir)
        )
        assert result["success"] is False
        assert "not empty" in result["error"]


class TestComplexWorkflow:
    """Test complex multi-tool workflows."""

    @pytest.mark.asyncio
    async def test_backup_and_restore_workflow(self, temp_dir):
        """Test backing up files and creating restore scripts."""
        # Create source directory with files
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        # Create various files to backup
        await write_file(str(source_dir / "config.json"), '{"backup": true}')
        await write_file(str(source_dir / "script.py"), "print('backup script')")
        (source_dir / "data").mkdir()
        await write_file(str(source_dir / "data" / "important.txt"), "Important data")

        # Create backup directory
        backup_dir = temp_dir / "backup"
        backup_dir.mkdir()

        # "Backup" by copying files (simplified)
        source_list = await list_directory(str(source_dir), recursive=True)
        assert "files" in source_list

        # Create backup script
        backup_script = f"""
import shutil
import os
from pathlib import Path

def backup_files():
    source = Path("{source_dir}")
    backup = Path("{backup_dir}")

    for item in source.rglob('*'):
        if item.is_file():
            relative_path = item.relative_to(source)
            backup_path = backup / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, backup_path)
            print(f"Backed up {{item}} to {{backup_path}}")

if __name__ == "__main__":
    backup_files()
"""

        await write_file(str(backup_dir / "backup.py"), backup_script)

        # Verify backup script was created
        script_result = await read_file(str(backup_dir / "backup.py"))
        assert script_result["success"] is True
        assert "backup_files" in script_result["content"]

    @pytest.mark.asyncio
    async def test_project_documentation_workflow(self, temp_dir):
        """Test creating project documentation."""
        project_dir = temp_dir / "documented_project"
        project_dir.mkdir()

        # Create project files
        await write_file(str(project_dir / "main.py"), "def main(): print('Hello')")
        await write_file(str(project_dir / "utils.py"), "def helper(): pass")

        # Create documentation
        readme_content = """# Documented Project

This project contains the following files:

## Files

"""
        # Get directory listing for documentation
        dir_result = await list_directory(str(project_dir))
        if "files" in dir_result:
            for item in dir_result["files"]:
                if item["type"] == "file" and item["size"] is not None:
                    readme_content += f"- `{item['name']}` ({item['size']} bytes)\n"

        readme_content += "\n## Usage\n\nRun `python main.py` to execute the main function."

        await write_file(str(project_dir / "README.md"), readme_content)

        # Verify documentation
        readme_result = await read_file(str(project_dir / "README.md"))
        assert readme_result["success"] is True
        assert "Documented Project" in readme_result["content"]
        assert "main.py" in readme_result["content"]


class TestPerformanceWorkflow:
    """Test performance aspects of workflows."""

    @pytest.mark.asyncio
    async def test_bulk_file_operations(self, temp_dir):
        """Test performance with bulk file operations."""
        bulk_dir = temp_dir / "bulk_test"
        bulk_dir.mkdir()

        # Create many files
        file_count = 50
        tasks = []

        for i in range(file_count):
            file_path = bulk_dir / f"file_{i:03d}.txt"
            content = f"Content of file {i}"
            tasks.append(write_file(str(file_path), content))

        # Execute all writes concurrently
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        assert all(result["success"] for result in results)
        assert len(results) == file_count

        # Verify files exist
        list_result = await list_directory(str(bulk_dir))
        assert "files" in list_result
        assert len(list_result["files"]) == file_count

    @pytest.mark.asyncio
    async def test_large_file_handling(self, temp_dir):
        """Test handling of large files."""
        large_file = temp_dir / "large_file.txt"

        # Create a moderately large file (1MB)
        large_content = "x" * (1024 * 1024)  # 1MB of 'x' characters

        write_result = await write_file(str(large_file), large_content)
        assert write_result["success"] is True

        # Read it back (but don't include content in result for large files)
        read_result = await read_file(str(large_file))
        assert read_result["success"] is True
        assert read_result["size"] == len(large_content)

        # File info should work
        info_result = await get_file_info(str(large_file))
        assert info_result["success"] is True
        assert info_result["size"] == len(large_content)
