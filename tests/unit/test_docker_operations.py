"""
Unit tests for Docker operations.

Tests all Docker operation functions with proper mocking and edge case coverage.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from filesystem_mcp.tools.docker_operations import (
    list_containers,
    get_docker_client
)


def parse_tool_result(result):
    """Parse the JSON content from a ToolResult."""
    return json.loads(result.content[0].text)


class TestGetDockerClient:
    """Test the get_docker_client function."""

    @patch('filesystem_mcp.tools.docker_operations.docker.from_env')
    def test_get_docker_client_success(self, mock_from_env):
        """Test successful Docker client creation."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_env.return_value = mock_client

        result = get_docker_client()

        assert result == mock_client
        mock_from_env.assert_called_once()

    @patch('filesystem_mcp.tools.docker_operations.docker.from_env')
    def test_get_docker_client_connection_error(self, mock_from_env):
        """Test Docker client creation when Docker is not available."""
        mock_from_env.side_effect = Exception("Connection refused")

        with pytest.raises(Exception) as exc_info:
            get_docker_client()

        assert "not running or not accessible" in str(exc_info.value)


class TestListContainers:
    """Test the list_containers function."""

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_success(self, mock_get_client):
        """Test successful container listing."""
        # Mock Docker client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock containers
        mock_container1 = Mock()
        mock_container1.id = "container1_id"
        mock_container1.name = "test_container_1"
        mock_container1.image = Mock()
        mock_container1.image.tags = ["nginx:latest"]
        mock_container1.status = "running"
        mock_container1.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {"Cmd": ["nginx"], "Env": []},
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}}
        }

        mock_container2 = Mock()
        mock_container2.id = "container2_id"
        mock_container2.name = "test_container_2"
        mock_container2.image = Mock()
        mock_container2.image.tags = ["redis:alpine"]
        mock_container2.status = "exited"
        mock_container2.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {"Cmd": ["redis-server"], "Env": []},
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}}
        }

        mock_client.containers.list.return_value = [mock_container1, mock_container2]

        result = await list_containers.run({"all_containers": True})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["total"] == 2
        assert len(data["containers"]) == 2

        # Check first container
        container1 = data["containers"][0]
        assert container1["id"] == "container1_id"
        assert container1["name"] == "test_container_1"
        assert container1["image"] == "nginx:latest"
        assert container1["status"] == "running"

        # Check second container
        container2 = data["containers"][1]
        assert container2["id"] == "container2_id"
        assert container2["name"] == "test_container_2"
        assert container2["image"] == "redis:alpine"
        assert container2["status"] == "exited"

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_no_containers(self, mock_get_client):
        """Test container listing when no containers exist."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.containers.list.return_value = []

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["total"] == 0
        assert data["containers"] == []

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_with_filters(self, mock_get_client):
        """Test container listing with filters."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_container = Mock()
        mock_container.id = "filtered_id"
        mock_container.name = "filtered_container"
        mock_container.image = Mock()
        mock_container.image.tags = ["nginx:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {"Cmd": ["nginx"], "Env": []},
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}}
        }

        mock_client.containers.list.return_value = [mock_container]

        filters = {"status": ["running"]}
        result = await list_containers.run({"filters": filters})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["containers"]) == 1
        mock_client.containers.list.assert_called_once_with(all=False, filters=filters)

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_running_only(self, mock_get_client):
        """Test listing only running containers."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_container = Mock()
        mock_container.id = "running_id"
        mock_container.name = "running_container"
        mock_container.image = Mock()
        mock_container.image.tags = ["nginx:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {"Cmd": ["nginx"], "Env": []},
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}}
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({"all_containers": False})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["containers"]) == 1
        mock_client.containers.list.assert_called_once_with(all=False, filters=None)

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_with_volumes(self, mock_get_client):
        """Test container listing with volume information."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_container = Mock()
        mock_container.id = "volume_id"
        mock_container.name = "volume_container"
        mock_container.image = Mock()
        mock_container.image.tags = ["mysql:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {"Cmd": ["mysqld"], "Env": []},
            "HostConfig": {
                "Binds": ["/host/path:/container/path:rw"],
                "PortBindings": {}
            },
            "NetworkSettings": {"Networks": {}}
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["containers"]) == 1

        container = data["containers"][0]
        assert "volumes" in container
        assert len(container["volumes"]) == 1
        assert container["volumes"][0]["host_path"] == "/host/path"
        assert container["volumes"][0]["container_path"] == "/container/path"
        assert container["volumes"][0]["mode"] == "rw"

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_with_labels(self, mock_get_client):
        """Test container listing with label information."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_container = Mock()
        mock_container.id = "labeled_id"
        mock_container.name = "labeled_container"
        mock_container.image = Mock()
        mock_container.image.tags = ["web:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {
                "Cmd": ["nginx"],
                "Env": [],
                "Labels": {"app": "web", "version": "1.0"}
            },
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}}
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["containers"]) == 1

        container = data["containers"][0]
        assert "labels" in container
        assert container["labels"]["app"] == "web"
        assert container["labels"]["version"] == "1.0"

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_with_ports(self, mock_get_client):
        """Test container listing with port mapping information."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_container = Mock()
        mock_container.id = "port_id"
        mock_container.name = "port_container"
        mock_container.image = Mock()
        mock_container.image.tags = ["nginx:latest"]
        mock_container.status = "running"
        mock_container.attrs = {
            "Created": "2024-01-01T09:00:00Z",
            "Config": {"Cmd": ["nginx"], "Env": []},
            "HostConfig": {
                "Binds": [],
                "PortBindings": {
                    "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
                    "443/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8443"}]
                }
            },
            "NetworkSettings": {"Networks": {}}
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["containers"]) == 1

        container = data["containers"][0]
        assert "ports" in container
        assert len(container["ports"]) == 2

        # Check port mappings
        ports = {p["container_port"]: p for p in container["ports"]}
        assert "80/tcp" in ports
        assert ports["80/tcp"]["host_port"] == "8080"
        assert "443/tcp" in ports
        assert ports["443/tcp"]["host_port"] == "8443"

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_large_result(self, mock_get_client):
        """Test handling of large numbers of containers."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Create 100 mock containers
        mock_containers = []
        for i in range(100):
            mock_container = Mock()
            mock_container.id = f"container_{i}_id"
            mock_container.name = f"container_{i}"
            mock_container.image = Mock()
            mock_container.image.tags = ["test:latest"]
            mock_container.status = "running"
            mock_container.attrs = {
                "Created": "2024-01-01T09:00:00Z",
                "Config": {"Cmd": ["test"], "Env": []},
                "HostConfig": {"Binds": [], "PortBindings": {}},
                "NetworkSettings": {"Networks": {}}
            }
            mock_containers.append(mock_container)

        mock_client.containers.list.return_value = mock_containers

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["total"] == 100
        assert len(data["containers"]) == 100

    @pytest.mark.asyncio
    @patch('filesystem_mcp.tools.docker_operations.get_docker_client')
    async def test_list_containers_docker_error(self, mock_get_client):
        """Test handling of Docker API errors."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.containers.list.side_effect = Exception("Docker API error")

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["status"] == "error"
        assert "Docker API error" in data["error"]
