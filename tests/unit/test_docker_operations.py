"""
Unit tests for Docker operations.

Tests all Docker operation functions with proper mocking and edge case coverage.
"""

import json
from unittest.mock import Mock, patch

import pytest

from filesystem_mcp.tools.docker_operations import (
    build_image,
    compose_config,
    compose_down,
    compose_logs,
    compose_ps,
    compose_up,
    container_exec,
    container_logs,
    container_stats,
    create_container,
    create_network,
    create_volume,
    get_container,
    get_docker_client,
    list_containers,
    list_images,
    list_networks,
    list_volumes,
    pull_image,
    remove_container,
    remove_image,
    remove_network,
    remove_volume,
    restart_container,
    start_container,
    stop_container,
)


def parse_tool_result(result):
    """Parse the JSON content from a ToolResult."""
    return json.loads(result.content[0].text)


class TestGetDockerClient:
    """Test the get_docker_client function."""

    @patch("filesystem_mcp.tools.docker_operations.docker.from_env")
    def test_get_docker_client_success(self, mock_from_env):
        """Test successful Docker client creation."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_env.return_value = mock_client

        result = get_docker_client()

        assert result == mock_client
        mock_from_env.assert_called_once()

    @patch("filesystem_mcp.tools.docker_operations.docker.from_env")
    def test_get_docker_client_connection_error(self, mock_from_env):
        """Test Docker client creation when Docker is not available."""
        mock_from_env.side_effect = Exception("Connection refused")

        with pytest.raises(Exception) as exc_info:
            get_docker_client()

        assert "not running or not accessible" in str(exc_info.value)


class TestListContainers:
    """Test the list_containers function."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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

        result = await list_containers.run({"all_containers": True})

        data = parse_tool_result(result)
        assert data["success"] is True
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
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
    async def test_list_containers_no_containers(self, mock_get_client):
        """Test container listing when no containers exist."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.containers.list.return_value = []

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["total"] == 0
        assert data["containers"] == []

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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

        filters = {"status": ["running"]}
        result = await list_containers.run({"filters": filters})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["containers"]) == 1
        mock_client.containers.list.assert_called_once_with(all=False, filters=filters)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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

        result = await list_containers.run({"all_containers": False})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["containers"]) == 1
        mock_client.containers.list.assert_called_once_with(all=False, filters=None)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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
            "HostConfig": {"Binds": ["/host/path:/container/path:rw"], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["containers"]) == 1

        container = data["containers"][0]
        assert "volumes" in container
        assert len(container["volumes"]) == 1
        assert container["volumes"][0]["host_path"] == "/host/path"
        assert container["volumes"][0]["container_path"] == "/container/path"
        assert container["volumes"][0]["mode"] == "rw"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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
            "Config": {"Cmd": ["nginx"], "Env": [], "Labels": {"app": "web", "version": "1.0"}},
            "HostConfig": {"Binds": [], "PortBindings": {}},
            "NetworkSettings": {"Networks": {}},
        }

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert len(data["containers"]) == 1

        container = data["containers"][0]
        assert "labels" in container
        assert container["labels"]["app"] == "web"
        assert container["labels"]["version"] == "1.0"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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

        mock_client.containers.list.return_value = [mock_container]

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["success"] is True
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
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
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

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert data["total"] == 100
        assert len(data["containers"]) == 100

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
    async def test_list_containers_docker_error(self, mock_get_client):
        """Test handling of Docker API errors."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.containers.list.side_effect = Exception("Docker API error")

        result = await list_containers.run({})

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "Docker API error" in data["error"]


class TestContainerOperations:
    """Test container management operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
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

        result = await get_container.run({"container_id": "test_container_id"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["container"]["id"] == "test_container_id"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_create_container_success(self, mock_get_client):
        """Test successful container creation."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.id = "new_container_id"
        mock_client.containers.create.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await create_container.run({"image": "nginx:latest", "name": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["container"]["id"] == "new_container_id"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_start_container_success(self, mock_get_client):
        """Test successful container start."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "exited"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await start_container.run({"container_id": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        mock_container.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_stop_container_success(self, mock_get_client):
        """Test successful container stop."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await stop_container.run({"container_id": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        mock_container.stop.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_restart_container_success(self, mock_get_client):
        """Test successful container restart."""
        mock_client = Mock()
        mock_container = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await restart_container.run({"container_id": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        mock_container.restart.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_remove_container_success(self, mock_get_client):
        """Test successful container removal."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "exited"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await remove_container.run({"container_id": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        mock_container.remove.assert_called_once_with(force=False, v=False)

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
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

        result = await container_exec.run(
            {"container_id": "test_container", "command": ["echo", "Hello World"]}
        )

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["exit_code"] == 0
        assert "Hello World" in data["output"]

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_container_logs_success(self, mock_get_client):
        """Test successful container log retrieval."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.logs.return_value = b"line 1\nline 2\n"
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_logs.run({"container_id": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert "line 1" in data["logs"]
        assert "line 2" in data["logs"]

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.containers.get_docker_client")
    async def test_container_stats_success(self, mock_get_client):
        """Test successful container statistics retrieval."""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = "running"
        mock_stats = {
            "cpu_stats": {"cpu_usage": {"total_usage": 1000}},
            "precpu_stats": {"cpu_usage": {"total_usage": 500}, "system_cpu_usage": 1000},
            "memory_stats": {"usage": 1024000},
        }
        mock_container.stats.return_value = mock_stats
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client

        result = await container_stats.run({"container_id": "test_container"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert "cpu_usage_percent" in data
        assert "memory_usage_bytes" in data


class TestImageOperations:
    """Test Docker image operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
    async def test_list_images_success(self, mock_get_client):
        """Test successful image listing."""
        mock_client = Mock()
        mock_image = Mock()
        mock_image.tags = ["nginx:latest"]
        mock_client.images.list.return_value = [mock_image]
        mock_get_client.return_value = mock_client

        result = await list_images.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["images"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
    async def test_pull_image_success(self, mock_get_client):
        """Test successful image pulling."""
        mock_client = Mock()
        mock_image = Mock()
        mock_image.tags = ["nginx:latest"]
        mock_client.images.get.return_value = mock_image
        mock_client.api.pull.return_value = None
        mock_get_client.return_value = mock_client

        result = await pull_image.run({"image_name": "nginx"})

        data = parse_tool_result(result)
        assert data["status"] == "success"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
    async def test_build_image_success(self, mock_get_client):
        """Test successful image building."""
        mock_client = Mock()
        mock_image = Mock()
        mock_image.tags = ["myapp:latest"]
        mock_client.images.build.return_value = (mock_image, [])
        mock_get_client.return_value = mock_client

        result = await build_image.run({"path": "/tmp/test", "tag": "myapp:latest"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["tag"] == "myapp:latest"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.images.get_docker_client")
    async def test_remove_image_success(self, mock_get_client):
        """Test successful image removal."""
        mock_client = Mock()
        mock_image = Mock()
        mock_client.images.get.return_value = mock_image
        mock_client.images.remove.return_value = [{"Deleted": "sha256:12345"}]
        mock_get_client.return_value = mock_client

        result = await remove_image.run({"image_id": "nginx:latest"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["deleted_layers"]) == 1


class TestNetworkOperations:
    """Test Docker network operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.networks_volumes.get_docker_client")
    async def test_list_networks_success(self, mock_get_client):
        """Test successful network listing."""
        mock_client = Mock()
        mock_network = Mock()
        mock_network.name = "bridge"
        mock_client.networks.list.return_value = [mock_network]
        mock_get_client.return_value = mock_client

        result = await list_networks.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["networks"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.networks_volumes.get_docker_client")
    async def test_create_network_success(self, mock_get_client):
        """Test successful network creation."""
        mock_client = Mock()
        mock_network = Mock()
        mock_network.name = "test_network"
        mock_client.networks.create.return_value = mock_network
        mock_get_client.return_value = mock_client

        result = await create_network.run({"name": "test_network", "driver": "bridge"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["network"]["name"] == "test_network"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.networks_volumes.get_docker_client")
    async def test_remove_network_success(self, mock_get_client):
        """Test successful network removal."""
        mock_client = Mock()
        mock_network = Mock()
        mock_client.networks.get.return_value = mock_network
        mock_get_client.return_value = mock_client

        result = await remove_network.run({"network_id": "test_network"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        mock_network.remove.assert_called_once()


class TestVolumeOperations:
    """Test Docker volume operations."""

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.networks_volumes.get_docker_client")
    async def test_list_volumes_success(self, mock_get_client):
        """Test successful volume listing."""
        mock_client = Mock()
        mock_volume = Mock()
        mock_volume.name = "test_volume"
        mock_client.volumes.list.return_value = [mock_volume]
        mock_get_client.return_value = mock_client

        result = await list_volumes.run({})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert len(data["volumes"]) == 1

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.networks_volumes.get_docker_client")
    async def test_create_volume_success(self, mock_get_client):
        """Test successful volume creation."""
        mock_client = Mock()
        mock_volume = Mock()
        mock_volume.name = "test_volume"
        mock_client.volumes.create.return_value = mock_volume
        mock_get_client.return_value = mock_client

        result = await create_volume.run({"name": "test_volume", "driver": "local"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        assert data["volume"]["name"] == "test_volume"

    @pytest.mark.asyncio
    @patch("filesystem_mcp.tools.docker_operations.networks_volumes.get_docker_client")
    async def test_remove_volume_success(self, mock_get_client):
        """Test successful volume removal."""
        mock_client = Mock()
        mock_volume = Mock()
        mock_client.volumes.get.return_value = mock_volume
        mock_get_client.return_value = mock_client

        result = await remove_volume.run({"volume_name": "test_volume"})

        data = parse_tool_result(result)
        assert data["status"] == "success"
        mock_volume.remove.assert_called_once()


class TestComposeOperations:
    """Test Docker Compose operations."""

    @pytest.mark.asyncio
    async def test_compose_up_success(self):
        """Test successful compose up."""
        with patch("filesystem_mcp.tools.docker_operations._run_compose_command") as mock_run:
            mock_run.return_value = (0, "Creating network...\nStarting services...", "")

            result = await compose_up.run({"path": "/tmp/compose"})

            data = parse_tool_result(result)
            assert data["status"] == "success"
            assert data["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_compose_down_success(self):
        """Test successful compose down."""
        with patch("filesystem_mcp.tools.docker_operations._run_compose_command") as mock_run:
            mock_run.return_value = (0, "Stopping services...\nRemoving containers...", "")

            result = await compose_down.run({"path": "/tmp/compose"})

            data = parse_tool_result(result)
            assert data["status"] == "success"
            assert data["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_compose_ps_success(self):
        """Test successful compose ps."""
        with patch("filesystem_mcp.tools.docker_operations._run_compose_command") as mock_run:
            mock_run.return_value = (
                0,
                "NAME                COMMAND             SERVICE             STATUS              PORTS",
                "",
            )

            result = await compose_ps.run({"path": "/tmp/compose"})

            data = parse_tool_result(result)
            assert data["status"] == "success"
            assert data["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_compose_logs_success(self):
        """Test successful compose logs."""
        with patch("filesystem_mcp.tools.docker_operations._run_compose_command") as mock_run:
            mock_run.return_value = (
                0,
                "web_1  | Starting nginx...\napi_1  | Starting server...",
                "",
            )

            result = await compose_logs.run({"path": "/tmp/compose"})

            data = parse_tool_result(result)
            assert data["status"] == "success"
            assert "nginx" in data["logs"]

    @pytest.mark.asyncio
    async def test_compose_config_success(self):
        """Test successful compose config validation."""
        with (
            patch("filesystem_mcp.tools.docker_operations._run_compose_command") as mock_run,
            patch("filesystem_mcp.tools.docker_operations._parse_compose_config") as mock_parse,
        ):
            mock_run.return_value = (0, "version: '3.8'\nservices:\n  web:\n    image: nginx", "")
            mock_parse.return_value = {"name": "test", "services": {"web": {"image": "nginx"}}}

            result = await compose_config.run({"path": "/tmp/compose"})

            data = parse_tool_result(result)
            assert data["status"] == "success"
            assert data["exit_code"] == 0
