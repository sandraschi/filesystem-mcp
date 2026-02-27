"""
Unit tests for FastMCP 2.14.3+ sampling integration and autonomous workflows.

Tests SEP-1577 sampling with tools functionality for file management automation.
"""


import pytest

from filesystem_mcp.tools.agentic_file_workflow import agentic_file_workflow


class TestSamplingIntegration:
    """Test sampling integration for autonomous file workflows."""

    @pytest.mark.asyncio
    async def test_basic_sampling_workflow(self, mock_sampling_context, mock_app_state):
        """Test basic autonomous file workflow with sampling."""
        # Setup mock sampling context
        mock_sampling_context.sample_step.side_effect = [
            # First step: analyze directory
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": "."}
                }
            },
            # Second step: read a file
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": "README.md"}
                }
            },
            None  # End workflow
        ]

        # Execute workflow
        result = await agentic_file_workflow(
            workflow_prompt="Analyze project structure and read main documentation",
            available_tools=["dir_ops", "file_ops", "search_ops"],
            max_iterations=3
        )

        # Verify workflow completed successfully
        assert result["success"] is True
        assert result["operation"] == "agentic_file_workflow"
        assert "iterations_completed" in result["result"]
        assert result["result"]["iterations_completed"] <= 3
        assert len(result["tools_executed"]) > 0

        # Verify sampling was called
        assert mock_sampling_context.sample_step.call_count >= 2

    @pytest.mark.asyncio
    async def test_sampling_workflow_file_organization(self, mock_sampling_context):
        """Test file organization workflow using sampling."""
        mock_sampling_context.sample_step.side_effect = [
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": "./src"}
                }
            },
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "move_file", "path": "temp.py", "destination_path": "utils/temp.py"}
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Organize Python files in src directory by moving utilities to utils folder",
            available_tools=["dir_ops", "file_ops"],
            max_iterations=5
        )

        assert result["success"] is True
        assert "organize" in result["result"]["workflow_prompt"].lower()
        assert result["quality_metrics"]["autonomous_execution"] is True

    @pytest.mark.asyncio
    async def test_sampling_workflow_backup_creation(self, mock_sampling_context):
        """Test backup workflow using sampling."""
        mock_sampling_context.sample_step.side_effect = [
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": "config.json"}
                }
            },
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "write_file", "path": "config.json.backup", "content": "{}"}
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Create backup of important configuration files",
            available_tools=["file_ops", "search_ops"],
            max_iterations=4
        )

        assert result["success"] is True
        assert "backup" in result["result"]["workflow_prompt"].lower()

    @pytest.mark.asyncio
    async def test_sampling_workflow_error_handling(self, mock_sampling_context):
        """Test error handling in sampling workflows."""
        # Simulate sampling failure
        mock_sampling_context.sample_step.side_effect = Exception("Sampling failed")

        result = await agentic_file_workflow(
            workflow_prompt="Analyze codebase structure",
            available_tools=["dir_ops", "file_ops"],
            max_iterations=2
        )

        # Should handle error gracefully
        assert result["success"] is False
        assert "error" in result
        assert "recovery_options" in result
        assert result["error_type"] == "SAMPLING_EXECUTION_ERROR"

    @pytest.mark.asyncio
    async def test_sampling_workflow_max_iterations(self, mock_sampling_context):
        """Test that workflows respect max_iterations limit."""
        # Never-ending workflow simulation
        mock_sampling_context.sample_step.return_value = {
            "tool_call": {
                "name": "dir_ops",
                "parameters": {"operation": "list_directory", "path": "."}
            }
        }

        result = await agentic_file_workflow(
            workflow_prompt="Continuous directory monitoring",
            available_tools=["dir_ops"],
            max_iterations=2  # Low limit to test
        )

        assert result["success"] is True
        assert result["result"]["iterations_completed"] <= 2
        assert result["result"]["max_iterations_allowed"] == 2

    @pytest.mark.asyncio
    async def test_sampling_workflow_missing_tools(self):
        """Test workflow with unavailable sampling context."""
        # Remove sampling context from app state
        from filesystem_mcp import app
        original_state = app.state.copy()
        app.state.pop("sampling_context", None)

        try:
            result = await agentic_file_workflow(
                workflow_prompt="Test workflow",
                available_tools=["file_ops"],
                max_iterations=1
            )

            assert result["success"] is False
            assert result["error_type"] == "SAMPLING_UNAVAILABLE"
            assert "recovery_options" in result

        finally:
            app.state.update(original_state)


class TestWorkflowQualityMetrics:
    """Test quality metrics and analytics for autonomous workflows."""

    @pytest.mark.asyncio
    async def test_workflow_metrics_calculation(self, mock_sampling_context):
        """Test that workflow metrics are properly calculated."""
        mock_sampling_context.sample_step.side_effect = [
            {"tool_call": {"name": "file_ops", "parameters": {"operation": "read_file"}}},
            {"tool_call": {"name": "dir_ops", "parameters": {"operation": "list_directory"}}},
            {"tool_call": {"name": "search_ops", "parameters": {"operation": "grep_file"}}},
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Comprehensive file analysis",
            available_tools=["file_ops", "dir_ops", "search_ops"],
            max_iterations=5
        )

        assert result["success"] is True
        metrics = result["quality_metrics"]
        assert "iterations_completed" in metrics
        assert "tools_executed" in metrics
        assert "unique_tools_used" in metrics
        assert "workflow_duration_seconds" in metrics
        assert "sampling_efficiency" in metrics
        assert metrics["autonomous_execution"] is True
        assert metrics["unique_tools_used"] == 3  # file_ops, dir_ops, search_ops

    @pytest.mark.asyncio
    async def test_workflow_efficiency_metrics(self, mock_sampling_context):
        """Test efficiency calculations in workflow metrics."""
        # Simulate efficient workflow with minimal iterations
        mock_sampling_context.sample_step.side_effect = [
            {"tool_call": {"name": "file_ops", "parameters": {"operation": "read_file"}}},
            None  # Complete in 1 iteration
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Quick file read",
            available_tools=["file_ops"],
            max_iterations=5
        )

        metrics = result["quality_metrics"]
        assert metrics["iterations_completed"] == 1
        assert metrics["tools_executed"] == 1
        assert metrics["sampling_efficiency"] == 1.0  # 1 tool per iteration

    @pytest.mark.asyncio
    async def test_workflow_recommendations(self, mock_sampling_context):
        """Test that workflows provide useful recommendations."""
        mock_sampling_context.sample_step.side_effect = [
            {"tool_call": {"name": "file_ops", "parameters": {"operation": "read_file"}}},
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Analyze file content",
            available_tools=["file_ops", "search_ops"],
            max_iterations=3
        )

        assert "recommendations" in result
        assert "next_steps" in result
        assert "related_operations" in result

        # Should suggest related operations
        assert len(result["related_operations"]) > 0
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["next_steps"], list)


class TestSamplingContextManagement:
    """Test sampling context state management."""

    def test_sampling_context_initialization(self, mock_sampling_context, mock_app_state):
        """Test that sampling context is properly initialized."""
        from filesystem_mcp import app

        assert "sampling_context" in app.state
        sampling_ctx = app.state["sampling_context"]
        assert sampling_ctx is mock_sampling_context

    def test_sampling_context_persistence(self, mock_sampling_context):
        """Test sampling context save/restore functionality."""
        # Test save state
        state = mock_sampling_context.save_state()
        assert state == {"test_state": True}

        # Test restore state
        mock_sampling_context.restore_state({"restored": True})
        mock_sampling_context.restore_state.assert_called_once_with({"restored": True})


class TestWorkflowValidation:
    """Test input validation for autonomous workflows."""

    @pytest.mark.asyncio
    async def test_empty_workflow_prompt(self):
        """Test validation of empty workflow prompt."""
        result = await agentic_file_workflow(
            workflow_prompt="",
            available_tools=["file_ops"],
            max_iterations=1
        )

        assert result["success"] is False
        assert result["error_type"] == "MISSING_WORKFLOW_PROMPT"
        assert "recovery_options" in result

    @pytest.mark.asyncio
    async def test_empty_available_tools(self):
        """Test validation of empty available tools list."""
        result = await agentic_file_workflow(
            workflow_prompt="Test workflow",
            available_tools=[],
            max_iterations=1
        )

        assert result["success"] is False
        assert result["error_type"] == "EMPTY_TOOLS_LIST"
        assert "suggested_fixes" in result

    @pytest.mark.asyncio
    async def test_none_workflow_prompt(self):
        """Test validation of None workflow prompt."""
        result = await agentic_file_workflow(
            workflow_prompt=None,
            available_tools=["file_ops"],
            max_iterations=1
        )

        assert result["success"] is False
        assert "MISSING_WORKFLOW_PROMPT" in result["error_type"]


class TestWorkflowScenarios:
    """Test specific workflow scenarios using sampling."""

    @pytest.mark.asyncio
    async def test_code_analysis_workflow(self, mock_sampling_context):
        """Test workflow for analyzing code files."""
        mock_sampling_context.sample_step.side_effect = [
            {
                "tool_call": {
                    "name": "search_ops",
                    "parameters": {"operation": "find_symbols", "path": "src", "pattern": "class|def"}
                }
            },
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": "src/main.py"}
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Analyze codebase structure and find main entry points",
            available_tools=["search_ops", "file_ops"],
            max_iterations=5
        )

        assert result["success"] is True
        assert "analyze" in result["result"]["workflow_prompt"].lower()
        assert len(result["tools_executed"]) >= 2

    @pytest.mark.asyncio
    async def test_data_processing_workflow(self, mock_sampling_context):
        """Test workflow for processing data files."""
        mock_sampling_context.sample_step.side_effect = [
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": "data"}
                }
            },
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "get_file_info", "path": "data/dataset.json"}
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Process and validate data files",
            available_tools=["dir_ops", "file_ops"],
            max_iterations=4
        )

        assert result["success"] is True
        assert "process" in result["result"]["workflow_prompt"].lower()
        assert "data" in result["result"]["workflow_prompt"].lower()
