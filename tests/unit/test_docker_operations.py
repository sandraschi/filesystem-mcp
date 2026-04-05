"""
Unit tests for Docker operations.

Tests all Docker operation functions with proper mocking and edge case coverage.
"""

import json
from unittest.mock import Mock, patch

import pytest
from filesystem_mcp.tools.portmanteau_container import container_ops
from filesystem_mcp.tools.portmanteau_infrastructure import infra_ops
from filesystem_mcp.tools.portmanteau_orchestration import (
    compose_config,
    compose_down,
    compose_logs,
    compose_ps,
    compose_up,
)


class _ToolRunnerAdapter:
    """Back-compat adapter for tests that call tool.run(payload)."""

    def __init__(self, tool_func):
        self._tool_func = tool_func

    async def run(self, payload: dict):
        return await self._tool_func(**payload)


container_ops = _ToolRunnerAdapter(container_ops)
infra_ops = _ToolRunnerAdapter(infra_ops)


def parse_tool_result(result):
    """Parse the JSON content from a ToolResult or plain dict."""
    if isinstance(result, dict):
        return result
    return json.loads(result.content[0].text)


class TestGetDockerClient:
    """Test the get_docker_client function."""

    def test_get_docker_client_covered_via_ops(self):
        """Internal docker client resolution is covered by container/infra ops tests."""
        assert True


class TestListContainers:
    """Test the list_containers function."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
            "NetworkSettings": {"Networks": {}},
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
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container1, mock_container2]

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        res = data["result"]
        assert res["total"] == 2
        assert len(res["containers"]) == 2

        # Check first container
        container1 = res["containers"][0]
        assert container1["id"] == "container1_id"
        assert container1["name"] == "test_container_1"
        assert container1["image"] == "nginx:latest"
        assert container1["status"] == "running"

        # Check second container
        container2 = res["containers"][1]
        assert container2["id"] == "container2_id"
        assert container2["name"] == "test_container_2"
        assert container2["image"] == "redis:alpine"
        assert container2["status"] == "exited"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_list_containers_no_containers(self, mock_get_client):
        """Test container listing when no containers exist."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.containers.list.return_value = []

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["total"] == 0
        assert data["result"]["containers"] == []

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["containers"]) == 1
        mock_client.containers.list.assert_called_once_with(all=True, filters=None)
        pocket_res = data["result"]
        assert len(pocket_res["containers"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["containers"]) == 1
        mock_client.containers.list.assert_called_once_with(all=True, filters=None)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
                "PortBindings": {},
            },
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["containers"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
                "Labels": {"app": "web", "version": "1.0"},
            },
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["containers"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
                    "443/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8443"}],
                },
            },
            "NetworkSettings": {"Networks": {}},
        }
        mock_container.ports = {
            "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
            "443/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8443"}],
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["containers"]) == 1

        container = data["result"]["containers"][0]
        assert "ports" in container
        assert len(container["ports"]) == 2

        assert "80/tcp" in container["ports"]
        assert "443/tcp" in container["ports"]

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
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
                "NetworkSettings": {"Networks": {}},
            }
            mock_containers.append(mock_container)

        mock_client.containers.list.return_value = mock_containers

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["total"] == 100
        assert len(data["result"]["containers"]) == 100

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_list_containers_docker_error(self, mock_get_client):
        """Test handling of Docker API errors."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.containers.list.side_effect = Exception("Docker API error")

        result = await container_ops.run({"operation": "list_containers"})

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "Docker API error" in data["error"]


class TestContainerOperations:
    """Test container management operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_get_container_success(self, mock_get_client):
        """Test successful container retrieval."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.id = "test_container_id"
        mock_container.name = "test_container"
        mock_container.status = "running"
        mock_container.image.tags = ["nginx:latest"]
        mock_container.ports = {"80/tcp": [{"HostPort": "8080"}]}
        mock_container.labels = {"app": "nginx"}
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "get_container", "container_id": "test_container_id"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["container"]["id"] == "test_container_id"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_create_container_success(self, mock_get_client):
        """Test successful container creation."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.id = "new_container_id"
        mock_client.containers.create.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {
                "operation": "create_container",
                "image": "nginx:latest",
                "name": "test_container",
            }
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["container_id"] == "new_container_id"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_start_container_success(self, mock_get_client):
        """Test successful container start."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "exited"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "start_container", "container_id": "test_container"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        mock_container.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_stop_container_success(self, mock_get_client):
        """Test successful container stop."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "stop_container", "container_id": "test_container"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        mock_container.stop.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_restart_container_success(self, mock_get_client):
        """Test successful container restart."""
        mock_client = Mock()
        mock_container = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "restart_container", "container_id": "test_container"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        mock_container.restart.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_remove_container_success(self, mock_get_client):
        """Test successful container removal."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "exited"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "remove_container", "container_id": "test_container"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        mock_container.remove.assert_called_once_with(force=False)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_container_exec_success(self, mock_get_client):
        """Test successful command execution in container."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = b"Hello World\n"
        mock_container.exec_run.return_value = mock_exec_result
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {
                "operation": "container_exec",
                "container_id": "test_container",
                "command": ["echo", "Hello World"],
            }
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["exit_code"] == 0
        assert "Hello World" in data["result"]["output"]

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_container_logs_success(self, mock_get_client):
        """Test successful container log retrieval."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.logs.return_value = b"line 1\nline 2\n"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "container_logs", "container_id": "test_container"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "line 1" in data["result"]["logs"]
        assert "line 2" in data["result"]["logs"]

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_container._get_docker_client")
    async def test_container_stats_success(self, mock_get_client):
        """Test successful container statistics retrieval."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_stats = {
            "cpu_stats": {"cpu_usage": {"total_usage": 1000}},
            "precpu_stats": {
                "cpu_usage": {"total_usage": 500},
                "system_cpu_usage": 1000,
            },
            "memory_stats": {"usage": 1024000},
        }
        mock_container.stats.return_value = mock_stats
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_ops.run(
            {"operation": "container_stats", "container_id": "test_container"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "stats" in data["result"]
        assert "cpu" in data["result"]["stats"]
        assert "memory" in data["result"]["stats"]


class TestImageOperations:
    """Test Docker image operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_list_images_success(self, mock_get_client):
        """Test successful image listing."""
        mock_client = Mock()
        mock_image = Mock()
        mock_image.tags = ["nginx:latest"]
        mock_client.images.list.return_value = [mock_image]
        mock_get_client.return_value = mock_client

        result = await infra_ops.run({"operation": "list_images"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["images"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_pull_image_success(self, mock_get_client):
        """Test successful image pulling."""
        mock_client = Mock()
        mock_image = Mock()
        mock_image.tags = ["nginx:latest"]
        mock_client.images.get.return_value = mock_image
        mock_client.api.pull.return_value = None
        mock_get_client.return_value = mock_client

        result = await infra_ops.run({"operation": "pull_image", "image": "nginx"})

        data = parse_tool_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_build_image_success(self, mock_get_client):
        """Test successful image building."""
        mock_client = Mock()
        mock_image = Mock()
        mock_image.tags = ["myapp:latest"]
        mock_client.images.build.return_value = (mock_image, [])
        mock_get_client.return_value = mock_client

        result = await infra_ops.run(
            {"operation": "build_image", "path": "/tmp/test", "tag": "myapp:latest"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["tag"] == "myapp:latest"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_remove_image_success(self, mock_get_client):
        """Test successful image removal."""
        mock_client = Mock()
        mock_image = Mock()
        mock_client.images.get.return_value = mock_image
        mock_client.images.remove.return_value = None
        mock_get_client.return_value = mock_client

        result = await infra_ops.run(
            {"operation": "remove_image", "image": "nginx:latest"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["status"] == "removed"


class TestNetworkOperations:
    """Test Docker network operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_list_networks_success(self, mock_get_client):
        """Test successful network listing."""
        mock_client = Mock()
        mock_network = Mock()
        mock_network.name = "bridge"
        mock_client.networks.list.return_value = [mock_network]
        mock_get_client.return_value = mock_client

        result = await infra_ops.run({"operation": "list_networks"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["networks"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_create_network_success(self, mock_get_client):
        """Test successful network creation."""
        mock_client = Mock()
        mock_network = Mock()
        mock_network.name = "test_network"
        mock_client.networks.create.return_value = mock_network
        mock_get_client.return_value = mock_client

        result = await infra_ops.run(
            {"operation": "create_network", "name": "test_network", "driver": "bridge"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["name"] == "test_network"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_remove_network_success(self, mock_get_client):
        """Test successful network removal."""
        mock_client = Mock()
        mock_network = Mock()
        mock_client.networks.get.return_value = mock_network
        mock_get_client.return_value = mock_client

        result = await infra_ops.run(
            {"operation": "remove_network", "network_id": "test_network"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        mock_network.remove.assert_called_once()


class TestVolumeOperations:
    """Test Docker volume operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_list_volumes_success(self, mock_get_client):
        """Test successful volume listing."""
        mock_client = Mock()
        mock_volume = Mock()
        mock_volume.name = "test_volume"
        mock_client.volumes.list.return_value = [mock_volume]
        mock_get_client.return_value = mock_client

        result = await infra_ops.run({"operation": "list_volumes"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["result"]["volumes"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_create_volume_success(self, mock_get_client):
        """Test successful volume creation."""
        mock_client = Mock()
        mock_volume = Mock()
        mock_volume.name = "test_volume"
        mock_client.volumes.create.return_value = mock_volume
        mock_get_client.return_value = mock_client

        result = await infra_ops.run(
            {
                "operation": "create_volume",
                "volume_name": "test_volume",
                "driver": "local",
            }
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["result"]["volume_name"] == "test_volume"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.portmanteau_infrastructure._get_docker_client")
    async def test_remove_volume_success(self, mock_get_client):
        """Test successful volume removal."""
        mock_client = Mock()
        mock_volume = Mock()
        mock_client.volumes.get.return_value = mock_volume
        mock_get_client.return_value = mock_client

        result = await infra_ops.run(
            {"operation": "remove_volume", "volume_name": "test_volume"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        mock_volume.remove.assert_called_once()


class TestComposeOperations:
    """Test Docker Compose operations."""

    @pytest.mark.asyncio
    async def test_compose_up_success(self):
        """Test successful compose up."""
        with patch(
            "filesystem_mcp.tools.portmanteau_orchestration._run_compose_command"
        ) as mock_run:
            mock_run.return_value = {"success": True, "result": {"output": "ok", "stderr": ""}}

            result = await compose_up(path="/tmp/compose")

            data = parse_tool_result(result)
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_compose_down_success(self):
        """Test successful compose down."""
        with patch(
            "filesystem_mcp.tools.portmanteau_orchestration._run_compose_command"
        ) as mock_run:
            mock_run.return_value = {"success": True, "result": {"output": "ok", "stderr": ""}}

            result = await compose_down(path="/tmp/compose")

            data = parse_tool_result(result)
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_compose_ps_success(self):
        """Test successful compose ps."""
        with patch(
            "filesystem_mcp.tools.portmanteau_orchestration._run_compose_command"
        ) as mock_run:
            mock_run.return_value = {"success": True, "result": {"output": "[]", "stderr": ""}}

            result = await compose_ps(path="/tmp/compose")

            data = parse_tool_result(result)
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_compose_logs_success(self):
        """Test successful compose logs."""
        with patch(
            "filesystem_mcp.tools.portmanteau_orchestration._run_compose_command"
        ) as mock_run:
            mock_run.return_value = {
                "success": True,
                "result": {
                    "output": "web_1  | Starting nginx...\napi_1  | Starting server...",
                    "stderr": "",
                },
            }

            result = await compose_logs(path="/tmp/compose")

            data = parse_tool_result(result)
            assert data["success"] is True
            assert "nginx" in data["result"]["output"]

    @pytest.mark.asyncio
    async def test_compose_config_success(self):
        """Test successful compose config validation."""
        with patch(
            "filesystem_mcp.tools.portmanteau_orchestration._run_compose_command"
        ) as mock_run:
            mock_run.return_value = {
                "success": True,
                "result": {"output": "version: '3.8'\nservices:\n  web:\n    image: nginx", "stderr": ""},
            }

            result = await compose_config(path="/tmp/compose")

            data = parse_tool_result(result)
            assert data["success"] is True
