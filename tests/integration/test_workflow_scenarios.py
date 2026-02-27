"""
Integration tests for autonomous file workflow scenarios.

Tests end-to-end sampling-based workflows using FastMCP 2.14.3+ autonomous execution.
"""


import pytest

from filesystem_mcp.tools.agentic_file_workflow import agentic_file_workflow


class TestFileOrganizationWorkflow:
    """Test file organization workflows using sampling."""

    @pytest.mark.asyncio
    async def test_project_cleanup_workflow(self, temp_dir, mock_sampling_context):
        """Test workflow that organizes and cleans up a messy project structure."""
        # Create a messy project structure
        (temp_dir / "script.py").write_text("# Main script")
        (temp_dir / "data.txt").write_text("some data")
        (temp_dir / "temp.tmp").write_text("temporary file")
        (temp_dir / "config.json").write_text('{"setting": "value"}')

        # Create subdirectories with misplaced files
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("# Utility functions")
        (src_dir / "readme.txt").write_text("Documentation")

        # Setup mock sampling to simulate file organization
        mock_sampling_context.sample_step.side_effect = [
            # Step 1: Analyze current structure
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": str(temp_dir)}
                }
            },
            # Step 2: Create organized directories
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "create_directory", "path": str(temp_dir / "scripts")}
                }
            },
            # Step 3: Move Python files to scripts
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "move_file",
                        "path": str(temp_dir / "script.py"),
                        "destination_path": str(temp_dir / "scripts" / "script.py")
                    }
                }
            },
            # Step 4: Move data files
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "move_file",
                        "path": str(temp_dir / "data.txt"),
                        "destination_path": str(temp_dir / "data" / "data.txt")
                    }
                }
            },
            # Step 5: Remove temp files
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "delete_file",
                        "path": str(temp_dir / "temp.tmp")
                    }
                }
            },
            None  # Complete workflow
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Organize this project by moving Python files to a scripts directory, data files to a data directory, and remove temporary files",
            available_tools=["dir_ops", "file_ops"],
            max_iterations=10
        )

        assert result["success"] is True
        assert result["quality_metrics"]["autonomous_execution"] is True
        assert len(result["tools_executed"]) >= 5

        # Verify the workflow actually organized files
        assert (temp_dir / "scripts" / "script.py").exists()
        assert not (temp_dir / "script.py").exists()  # Should be moved
        assert not (temp_dir / "temp.tmp").exists()  # Should be deleted


class TestCodeAnalysisWorkflow:
    """Test code analysis and documentation workflows."""

    @pytest.mark.asyncio
    async def test_codebase_analysis_workflow(self, temp_dir, mock_sampling_context):
        """Test workflow that analyzes a codebase and generates documentation."""
        # Create a sample Python project
        main_py = temp_dir / "main.py"
        main_py.write_text('''
def hello_world():
    """Print hello world."""
    print("Hello, World!")

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

if __name__ == "__main__":
    hello_world()
    result = calculate_sum(5, 3)
    print(f"Sum: {result}")
''')

        utils_py = temp_dir / "utils.py"
        utils_py.write_text('''
import os

def get_file_size(filepath):
    """Get file size in bytes."""
    return os.path.getsize(filepath)

def list_directory(path):
    """List contents of directory."""
    return os.listdir(path)
''')

        # Setup mock sampling for code analysis
        mock_sampling_context.sample_step.side_effect = [
            # Step 1: Analyze project structure
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": str(temp_dir)}
                }
            },
            # Step 2: Read main file
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": str(main_py)}
                }
            },
            # Step 3: Analyze functions
            {
                "tool_call": {
                    "name": "search_ops",
                    "parameters": {
                        "operation": "find_symbols",
                        "path": str(temp_dir),
                        "pattern": "def "
                    }
                }
            },
            # Step 4: Generate documentation
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "write_file",
                        "path": str(temp_dir / "README.md"),
                        "content": "# Sample Python Project\n\nContains utility functions and a main script."
                    }
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Analyze this Python codebase, identify all functions, and generate project documentation",
            available_tools=["dir_ops", "file_ops", "search_ops"],
            max_iterations=8
        )

        assert result["success"] is True
        assert "analyze" in result["result"]["workflow_prompt"].lower()
        assert len(result["tools_executed"]) >= 4

        # Should have created documentation
        readme = temp_dir / "README.md"
        assert readme.exists()
        assert "Python Project" in readme.read_text()


class TestDataProcessingWorkflow:
    """Test data processing and validation workflows."""

    @pytest.mark.asyncio
    async def test_data_validation_workflow(self, temp_dir, mock_sampling_context):
        """Test workflow that validates and processes data files."""
        # Create sample data files
        valid_json = temp_dir / "data.json"
        valid_json.write_text('{"name": "test", "value": 123}')

        invalid_json = temp_dir / "invalid.json"
        invalid_json.write_text('{"name": "test", "value": }')  # Invalid JSON

        csv_file = temp_dir / "data.csv"
        csv_file.write_text("name,value\ntest,123\nother,456")

        # Setup mock sampling for data validation
        mock_sampling_context.sample_step.side_effect = [
            # Step 1: List data files
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": str(temp_dir)}
                }
            },
            # Step 2: Validate JSON files
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": str(valid_json)}
                }
            },
            # Step 3: Check invalid JSON
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": str(invalid_json)}
                }
            },
            # Step 4: Process valid data
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "write_file",
                        "path": str(temp_dir / "processed_data.json"),
                        "content": '{"processed": true, "records": 2}'
                    }
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Validate JSON and CSV data files, process valid data, and report any issues",
            available_tools=["dir_ops", "file_ops", "search_ops"],
            max_iterations=7
        )

        assert result["success"] is True
        assert "validate" in result["result"]["workflow_prompt"].lower()
        assert len(result["tools_executed"]) >= 4

        # Should have created processed data file
        processed = temp_dir / "processed_data.json"
        assert processed.exists()


class TestBackupAndRecoveryWorkflow:
    """Test backup creation and recovery workflows."""

    @pytest.mark.asyncio
    async def test_backup_workflow(self, temp_dir, mock_sampling_context):
        """Test workflow that creates backups of important files."""
        # Create important files
        config = temp_dir / "config.ini"
        config.write_text("[settings]\nkey=value")

        database = temp_dir / "database.db"
        database.write_text("database content")

        # Setup mock sampling for backup creation
        mock_sampling_context.sample_step.side_effect = [
            # Step 1: Identify important files
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": str(temp_dir)}
                }
            },
            # Step 2: Create backup directory
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "create_directory", "path": str(temp_dir / "backup")}
                }
            },
            # Step 3: Backup config file
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "read_file",
                        "path": str(config)
                    }
                }
            },
            # Step 4: Write backup
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "write_file",
                        "path": str(temp_dir / "backup" / "config.ini.bak"),
                        "content": "[settings]\nkey=value"
                    }
                }
            },
            # Step 5: Backup database
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "read_file",
                        "path": str(database)
                    }
                }
            },
            # Step 6: Write database backup
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "write_file",
                        "path": str(temp_dir / "backup" / "database.db.bak"),
                        "content": "database content"
                    }
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Create backups of all important files in the project",
            available_tools=["dir_ops", "file_ops"],
            max_iterations=10
        )

        assert result["success"] is True
        assert "backup" in result["result"]["workflow_prompt"].lower()
        assert len(result["tools_executed"]) >= 6

        # Verify backups were created
        backup_dir = temp_dir / "backup"
        assert backup_dir.exists()
        assert (backup_dir / "config.ini.bak").exists()
        assert (backup_dir / "database.db.bak").exists()


class TestErrorHandlingWorkflow:
    """Test error handling in autonomous workflows."""

    @pytest.mark.asyncio
    async def test_workflow_with_errors(self, temp_dir, mock_sampling_context):
        """Test workflow that encounters and handles errors gracefully."""
        # Create a file that will cause issues
        readonly_file = temp_dir / "readonly.txt"
        readonly_file.write_text("content")
        readonly_file.chmod(0o444)  # Make readonly

        # Setup mock sampling that will try to modify readonly file
        mock_sampling_context.sample_step.side_effect = [
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "edit_file",
                        "path": str(readonly_file),
                        "old_string": "content",
                        "new_string": "modified"
                    }
                }
            },
            # After error, try a different approach
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "read_file",
                        "path": str(readonly_file)
                    }
                }
            },
            # Create a new file instead
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {
                        "operation": "write_file",
                        "path": str(temp_dir / "modified.txt"),
                        "content": "modified content"
                    }
                }
            },
            None
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Modify the readonly file and create a new version",
            available_tools=["file_ops"],
            max_iterations=5
        )

        assert result["success"] is True  # Workflow should complete despite errors
        assert len(result["tools_executed"]) >= 3

        # Should have created the alternative file
        modified_file = temp_dir / "modified.txt"
        assert modified_file.exists()
        assert modified_file.read_text() == "modified content"


class TestWorkflowPerformance:
    """Test workflow performance and efficiency metrics."""

    @pytest.mark.asyncio
    async def test_efficient_workflow_execution(self, temp_dir, mock_sampling_context):
        """Test that workflows execute efficiently with good metrics."""
        # Create simple file structure
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")

        # Setup efficient workflow
        mock_sampling_context.sample_step.side_effect = [
            {
                "tool_call": {
                    "name": "dir_ops",
                    "parameters": {"operation": "list_directory", "path": str(temp_dir)}
                }
            },
            {
                "tool_call": {
                    "name": "file_ops",
                    "parameters": {"operation": "read_file", "path": str(temp_dir / "file1.txt")}
                }
            },
            None  # Complete efficiently
        ]

        result = await agentic_file_workflow(
            workflow_prompt="Quickly check the contents of text files in the directory",
            available_tools=["dir_ops", "file_ops"],
            max_iterations=5
        )

        assert result["success"] is True

        # Check performance metrics
        metrics = result["quality_metrics"]
        assert "iterations_completed" in metrics
        assert "tools_executed" in metrics
        assert "sampling_efficiency" in metrics
        assert "workflow_duration_seconds" in metrics

        # Should be efficient (low iterations for simple task)
        assert metrics["iterations_completed"] <= 3
        assert metrics["sampling_efficiency"] > 0
