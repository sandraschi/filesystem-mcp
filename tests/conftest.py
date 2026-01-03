"""
Pytest configuration and fixtures for filesystem-mcp tests.

This file contains shared fixtures and configuration for all tests.
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp(prefix="filesystem_mcp_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content")
    yield file_path


@pytest.fixture
def temp_repo(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary Git repository for testing."""
    import git

    repo_path = temp_dir / "test_repo"
    repo_path.mkdir()

    # Initialize repository
    repo = git.Repo.init(repo_path)

    # Create initial commit
    test_file = repo_path / "README.md"
    test_file.write_text("# Test Repository\n\nThis is a test repository.")
    repo.index.add([str(test_file.relative_to(repo_path))])
    repo.index.commit("Initial commit")

    yield repo_path
