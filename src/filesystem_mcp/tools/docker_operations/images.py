"""
Docker image management operations for the Filesystem MCP.

This module provides comprehensive image lifecycle management including
listing, pulling, building, and removal operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
from enum import Enum

import docker
from docker.errors import DockerException, APIError, NotFound, ImageNotFound, BuildError

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Configure structured logging for this module
logger = logging.getLogger(__name__)

# Import app locally in functions to avoid circular imports
def _get_app():
    """Get the app instance locally to avoid circular imports."""
    import sys
    import os
    # Add src to path if not already there
    src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    import filesystem_mcp
    return filesystem_mcp.app


# Pydantic models for image operations
class DockerImageInfo(BaseModel):
    """Comprehensive Docker image information."""
    id: str
    repo_tags: List[str] = Field(default_factory=list)
    repo_digests: List[str] = Field(default_factory=list)
    parent: Optional[str] = None
    comment: Optional[str] = None
    created: Optional[datetime] = None
    container: Optional[str] = None
    docker_version: Optional[str] = None
    author: Optional[str] = None
    architecture: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    size: int
    virtual_size: Optional[int] = None
    graph_driver: Dict[str, Any] = Field(default_factory=dict)
    root_fs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DockerOperationStatus(str, Enum):
    """Status enumeration for Docker operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ImageListResponse(BaseModel):
    """Response model for image listing operations."""
    status: DockerOperationStatus
    images: List[DockerImageInfo] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ImageResponse(BaseModel):
    """Response model for single image operations."""
    status: DockerOperationStatus
    image: Optional[DockerImageInfo] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ImageBuildRequest(BaseModel):
    """Request model for image building."""
    path: str
    dockerfile: str = "Dockerfile"
    tag: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    buildargs: Dict[str, str] = Field(default_factory=dict)
    nocache: bool = False
    pull: bool = False
    rm: bool = True
    forcerm: bool = False
    squash: bool = False
    network_mode: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


def get_docker_client():
    """Get Docker client with proper error handling."""
    try:
        client = docker.from_env()
        # Test the connection
        client.ping()
        return client
    except DockerException as e:
        logger.error(f"Failed to connect to Docker daemon: {e}")
        raise Exception("Docker daemon is not running or not accessible") from e


@_get_app().tool()
async def list_images(
    all_images: bool = False,
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """List Docker images with detailed information and filtering options.

    Retrieves comprehensive information about Docker images including tags,
    sizes, creation dates, and architecture details.

    Args:
        all_images: If True, show all images including intermediate layers
        filters: Dictionary of filters to apply (e.g., {"dangling": ["true"]})

    Returns:
        Dictionary containing image list and metadata

    Error Handling:
        Returns error information if Docker daemon is not accessible
    """
    try:
        client = get_docker_client()
        images = client.images.list(all=all_images, filters=filters or {})

        image_list = []
        for image in images:
            try:
                image_list.append(_parse_image_info(image))
            except Exception as e:
                logger.warning(f"Failed to parse image {image.id}: {e}")

        return ImageListResponse(
            status=DockerOperationStatus.SUCCESS,
            images=image_list,
            total=len(image_list)
        )

    except Exception as e:
        return ImageListResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to list images: {str(e)}"
        )


@_get_app().tool()
async def get_image(image_id: str) -> dict:
    """Get detailed information about a specific Docker image.

    Retrieves comprehensive information about an image including its layers,
    configuration, and metadata.

    Args:
        image_id: Image ID, tag, or digest

    Returns:
        Dictionary containing image information and metadata

    Error Handling:
        Returns error information if image not found or Docker daemon inaccessible
    """
    try:
        client = get_docker_client()
        image = client.images.get(image_id)

        image_info = _parse_image_info(image)

        return ImageResponse(
            status=DockerOperationStatus.SUCCESS,
            image=image_info
        )

    except ImageNotFound:
        return ImageResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Image '{image_id}' not found"
        )
    except Exception as e:
        return ImageResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to get image info: {str(e)}"
        )


@_get_app().tool()
async def pull_image(
    image_name: str,
    tag: str = "latest",
    all_tags: bool = False,
    platform: Optional[str] = None
) -> dict:
    """Pull a Docker image from a registry.

    Downloads an image from Docker Hub or other registries with progress tracking.

    Args:
        image_name: Image name (e.g., 'nginx', 'ubuntu')
        tag: Image tag (default: 'latest')
        all_tags: Pull all tags for the image
        platform: Target platform (e.g., 'linux/amd64', 'linux/arm64')

    Returns:
        Dictionary containing pull result and metadata

    Error Handling:
        Returns error information if image not found or pull fails
    """
    try:
        client = get_docker_client()

        full_image_name = f"{image_name}:{tag}" if tag and not all_tags else image_name

        # Pull the image
        if all_tags:
            # Pull all tags - this might take a while
            logger.info(f"Pulling all tags for {image_name}")
            result = client.api.pull(image_name, all=True, platform=platform)
        else:
            logger.info(f"Pulling {full_image_name}")
            result = client.api.pull(full_image_name, platform=platform)

        # Get the pulled image info
        if all_tags:
            # For all_tags, we can't easily get a single image object
            return {
                "status": DockerOperationStatus.SUCCESS,
                "message": f"Successfully pulled all tags for '{image_name}'",
                "image_name": image_name,
                "all_tags": True
            }
        else:
            # Get the specific image that was pulled
            image = client.images.get(full_image_name)
            image_info = _parse_image_info(image)

            return ImageResponse(
                status=DockerOperationStatus.SUCCESS,
                image=image_info
            )

    except ImageNotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Image '{full_image_name}' not found in registry"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to pull image: {str(e)}"
        }


@_get_app().tool()
async def build_image(
    path: str,
    dockerfile: str = "Dockerfile",
    tag: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
    buildargs: Optional[Dict[str, str]] = None,
    nocache: bool = False,
    pull: bool = False,
    rm: bool = True,
    forcerm: bool = False,
    squash: bool = False,
    network_mode: Optional[str] = None
) -> dict:
    """Build a Docker image from a Dockerfile.

    Builds an image from source code with full control over build parameters.

    Args:
        path: Path to the build context directory
        dockerfile: Name of the Dockerfile (default: 'Dockerfile')
        tag: Tag for the built image (optional)
        labels: Labels to add to the image
        buildargs: Build-time variables
        nocache: Do not use cache when building
        pull: Always attempt to pull a newer version of the image
        rm: Remove intermediate containers after a successful build
        forcerm: Always remove intermediate containers
        squash: Squash the resulting image layers into a single layer
        network_mode: Network mode for the build

    Returns:
        Dictionary containing build result and metadata

    Error Handling:
        Returns error information if build fails or path not found
    """
    try:
        from pathlib import Path

        client = get_docker_client()

        build_path = Path(path).resolve()
        if not build_path.exists():
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Build context path '{path}' not found"
            }

        if not build_path.is_dir():
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Build context '{path}' is not a directory"
            }

        dockerfile_path = build_path / dockerfile
        if not dockerfile_path.exists():
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Dockerfile '{dockerfile}' not found in '{path}'"
            }

        # Prepare build configuration
        build_config = {
            'path': str(build_path),
            'dockerfile': dockerfile,
            'nocache': nocache,
            'pull': pull,
            'rm': rm,
            'forcerm': forcerm,
        }

        if tag:
            build_config['tag'] = tag
        if labels:
            build_config['labels'] = labels
        if buildargs:
            build_config['buildargs'] = buildargs
        if network_mode:
            build_config['network_mode'] = network_mode
        if squash:
            build_config['squash'] = squash

        logger.info(f"Building image from {path} with tag {tag or 'latest'}")

        # Build the image
        image, build_logs = client.images.build(**build_config)

        # Parse build logs
        logs_output = []
        for log_entry in build_logs:
            if 'stream' in log_entry:
                logs_output.append(log_entry['stream'].rstrip())
            elif 'error' in log_entry:
                logs_output.append(f"ERROR: {log_entry['error']}")
            elif 'status' in log_entry:
                logs_output.append(f"STATUS: {log_entry['status']}")

        image_info = _parse_image_info(image)

        return {
            "status": DockerOperationStatus.SUCCESS,
            "image": image_info,
            "build_logs": '\n'.join(logs_output),
            "build_path": str(build_path),
            "dockerfile": dockerfile,
            "tag": tag
        }

    except BuildError as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Build failed: {str(e)}",
            "build_logs": str(e)
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to build image: {str(e)}"
        }


@_get_app().tool()
async def remove_image(
    image_id: str,
    force: bool = False,
    noprune: bool = False
) -> dict:
    """Remove a Docker image.

    Removes an image from the local Docker daemon. Use force=True to remove
    images that are being used by containers.

    Args:
        image_id: Image ID, tag, or digest to remove
        force: Force removal even if image is being used
        noprune: Do not delete untagged parent images

    Returns:
        Dictionary containing removal result and metadata

    Error Handling:
        Returns error information if image not found or removal fails
    """
    try:
        client = get_docker_client()

        # Check if image exists first
        try:
            image = client.images.get(image_id)
        except ImageNotFound:
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Image '{image_id}' not found"
            }

        # Remove the image
        removal_result = client.images.remove(image=image_id, force=force, noprune=noprune)

        # Parse removal result (usually contains deleted layers info)
        deleted_layers = []
        if isinstance(removal_result, list):
            for item in removal_result:
                if 'Deleted' in item:
                    deleted_layers.append(item['Deleted'])
                elif 'Untagged' in item:
                    deleted_layers.append(f"Untagged: {item['Untagged']}")

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": f"Image '{image_id}' removed successfully",
            "image_id": image_id,
            "deleted_layers": deleted_layers,
            "force_used": force,
            "prune_disabled": noprune
        }

    except ImageNotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Image '{image_id}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to remove image: {str(e)}"
        }


@_get_app().tool()
async def prune_images(
    all_images: bool = False,
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """Prune unused Docker images.

    Removes dangling images and optionally all unused images to free up disk space.

    Args:
        all_images: Remove all unused images (not just dangling)
        filters: Additional filters for image pruning

    Returns:
        Dictionary containing pruning results and space freed

    Error Handling:
        Returns error information if pruning fails
    """
    try:
        client = get_docker_client()

        # Prune images
        if all_images:
            # Prune all unused images
            result = client.images.prune(filters=filters or {})
        else:
            # Prune only dangling images
            result = client.images.prune(filters={"dangling": ["true"]})

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": f"Successfully pruned {'all unused' if all_images else 'dangling'} images",
            "space_reclaimed": result.get('SpaceReclaimed', 0),
            "images_deleted": result.get('ImagesDeleted', []),
            "all_images": all_images
        }

    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to prune images: {str(e)}"
        }


def _parse_image_info(image) -> DockerImageInfo:
    """
    Parse Docker image object into a structured DockerImageInfo object.

    Args:
        image: Docker image object

    Returns:
        DockerImageInfo with parsed image details
    """
    attrs = image.attrs

    # Parse creation time
    created = None
    if 'Created' in attrs:
        try:
            # Docker timestamps are in ISO format
            created_str = attrs['Created']
            if created_str.endswith('Z'):
                created_str = created_str[:-1] + '+00:00'
            created = datetime.fromisoformat(created_str)
        except (ValueError, TypeError):
            pass

    return DockerImageInfo(
        id=image.id,
        repo_tags=image.tags or [],
        repo_digests=getattr(image, 'digests', []) or [],
        parent=attrs.get('Parent'),
        comment=attrs.get('Comment'),
        created=created,
        container=attrs.get('Container'),
        docker_version=attrs.get('DockerVersion'),
        author=attrs.get('Author'),
        architecture=attrs.get('Architecture'),
        os=attrs.get('Os'),
        os_version=attrs.get('OsVersion'),
        size=attrs.get('Size', 0),
        virtual_size=attrs.get('VirtualSize'),
        graph_driver=attrs.get('GraphDriver', {}),
        root_fs=attrs.get('RootFS', {}),
        metadata={
            'labels': attrs.get('Config', {}).get('Labels', {}),
            'env': attrs.get('Config', {}).get('Env', []),
            'cmd': attrs.get('Config', {}).get('Cmd', []),
            'entrypoint': attrs.get('Config', {}).get('Entrypoint'),
            'working_dir': attrs.get('Config', {}).get('WorkingDir'),
            'user': attrs.get('Config', {}).get('User'),
        }
    )
