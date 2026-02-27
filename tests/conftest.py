"""
Pytest configuration and fixtures for filesystem-mcp tests.

This file contains shared fixtures and configuration for all tests.
Supports FastMCP 2.14.3+ with enhanced response patterns and sampling.
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

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


@pytest.fixture
def mock_sampling_context():
    """Create a mock sampling context for testing autonomous workflows."""
    mock_context = MagicMock()

    # Mock sampling step method
    async def mock_sample_step(prompt, available_tools, context, operation_type):
        # Simulate LLM decision making for file operations
        if "organize" in prompt.lower():
            return {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": "."}
                }
            }
        elif "backup" in prompt.lower():
            return {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": "important.txt"}
                }
            }
        else:
            return None

    mock_context.sample_step = AsyncMock(side_effect=mock_sample_step)
    mock_context.save_state.return_value = {"test_state": True}
    mock_context.restore_state.return_value = None

    return mock_context


@pytest.fixture
def mock_app_state(mock_sampling_context):
    """Create a mock app state with sampling context."""
    return {"sampling_context": mock_sampling_context}


@pytest.fixture(autouse=True)
def mock_app_state_fixture(mock_app_state, monkeypatch):
    """Automatically mock the app state for all tests."""
    from filesystem_mcp import app
    # FastMCP doesn't have a state attribute, so we need to add it dynamically
    if not hasattr(app, 'state'):
        app.state = {}
    original_state = app.state.copy()
    app.state.update(mock_app_state)
    yield
    app.state.clear()
    app.state.update(original_state)


def parse_enhanced_response(response: dict) -> dict:
    """Parse enhanced FastMCP 2.14.3+ response format."""
    if not isinstance(response, dict):
        return response

    # Handle different response types
    if response.get("status") == "clarification_needed":
        return {
            "type": "clarification",
            "ambiguities": response.get("ambiguities", []),
            "options": response.get("options", {}),
            "suggested_questions": response.get("suggested_questions", []),
            "preserved_context": response.get("preserved_context"),
        }

    if response.get("success") is False:
        return {
            "type": "error",
            "success": False,
            "error": response.get("error"),
            "error_type": response.get("error_type"),
            "recovery_options": response.get("recovery_options", []),
            "suggested_fixes": response.get("suggested_fixes", []),
            "diagnostic_info": response.get("diagnostic_info", {}),
        }

    if response.get("success") is True:
        return {
            "type": "success",
            "success": True,
            "result": response.get("result", {}),
            "execution_time_ms": response.get("execution_time_ms"),
            "quality_metrics": response.get("quality_metrics", {}),
            "recommendations": response.get("recommendations", []),
            "next_steps": response.get("next_steps", []),
            "related_operations": response.get("related_operations", []),
        }

    return response


def assert_enhanced_success_response(response: dict, required_fields: list = None):
    """Assert that a response follows the enhanced success pattern."""
    assert response["success"] is True
    assert "result" in response
    assert "execution_time_ms" in response
    assert "quality_metrics" in response
    assert "recommendations" in response
    assert "next_steps" in response
    assert "related_operations" in response

    if required_fields:
        for field in required_fields:
            assert field in response["result"]


def assert_enhanced_error_response(response: dict):
    """Assert that a response follows the enhanced error pattern."""
    assert response["success"] is False
    assert "error" in response
    assert "error_type" in response
    assert "recovery_options" in response
    assert "diagnostic_info" in response


def assert_clarification_response(response: dict):
    """Assert that a response follows the clarification pattern."""
    assert response["status"] == "clarification_needed"
    assert "ambiguities" in response
    assert "suggested_questions" in response
