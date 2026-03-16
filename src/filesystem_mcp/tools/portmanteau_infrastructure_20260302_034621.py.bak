import logging
from typing import Any, Literal, Optional

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _get_docker_client,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
async def infra_ops(
    operation: Literal[
        "list_images",
        "get_image",
        "pull_image",
        "build_image",
        "remove_image",
        "prune_images",
        "list_networks",
        "get_network",
        "create_network",
        "remove_network",
        "prune_networks",
        "list_volumes",
        "get_volume",
        "create_volume",
        "remove_volume",
        "prune_volumes",
    ],
    image: Optional[str] = None,
    tag: str = "latest",
    network_id: Optional[str] = None,
    volume_name: Optional[str] = None,
    name: Optional[str] = None,
    all_images: bool = False,
    platform: Optional[str] = None,
    nocache: bool = False,
    pull: bool = False,
    rm: bool = True,
    forcerm: bool = False,
    squash: bool = False,
    dockerfile: str = "Dockerfile",
    path: Optional[str] = None,
    buildargs: Optional[dict[str, str]] = None,
    noprune: bool = False,
    driver: Optional[str] = None,
    options: Optional[dict[str, str]] = None,
    ipam: Optional[dict[str, Any]] = None,
    internal: bool = False,
    attachable: bool = False,
    ingress: bool = False,
    enable_ipv6: bool = False,
    labels: Optional[dict[str, str]] = None,
    driver_opts: Optional[dict[str, str]] = None,
    filters: Optional[dict[str, list[str]]] = None,
    force: bool = False,
) -> dict[str, Any]:
    """Docker Images, Networks, and Volumes operations.

    Args:
        operation (Literal, required): Available infrastructure operations:
            - "list_images": List local images
            - "get_image": Image metadata (requires: image)
            - "pull_image": Download image (requires: image)
            - "build_image": Create image from Dockerfile (requires: path)
            - "remove_image": Delete image (requires: image)
            - "prune_images": Cleanup unused images
            - "list_networks": List Docker networks
            - "get_network": Network info (requires: network_id)
            - "create_network": New network (requires: name)
            - "remove_network": Delete network (requires: network_id)
            - "prune_networks": Cleanup networks
            - "list_volumes": List Docker volumes
            - "get_volume": Volume info (requires: volume_name)
            - "create_volume": New volume (requires: volume_name)
            - "remove_volume": Delete volume (requires: volume_name)
            - "prune_volumes": Cleanup volumes

        --- IDENTIFIERS ---

        image (str | None): Image name/ID
        tag (str): Image tag. Default: "latest"
        network_id (str | None): Network ID or name
        volume_name (str | None): Volume name
        name (str | None): Name for new net/vol

        --- IMAGE OPTIONS ---

        all_images (bool): Show intermediate images. Default: False
        platform (str | None): Target platform
        nocache (bool): Bypass build cache. Default: False
        pull (bool): Pull fresh base images. Default: False
        rm/forcerm (bool): Intermediate container removal
        squash (bool): Flatten layers
        dockerfile (str): Dockerfile filename. Default: "Dockerfile"
        path (str | None): Build context path
        buildargs (Dict | None): Build variables
        noprune (bool): Keep parent images on removal. Default: False

        --- NETWORK & VOLUME OPTIONS ---

        driver (str | None): Driver type (bridge, overlay, local, etc.)
        options (Dict | None): Driver-specific options
        ipam (Dict | None): IP management config
        internal (bool): Isolated network. Default: False
        attachable (bool): Manual container attachment. Default: False
        ingress (bool): Swarm routing mesh. Default: False
        enable_ipv6 (bool): IPv6 support. Default: False
        labels (Dict | None): Metadata labels
        driver_opts (Dict | None): Volume driver options

        --- GENERAL ---

        filters (Dict | None): Filter criteria
        force (bool): Forced removal. Default: False
    """
    try:
        if not operation:
            return _clarification_response(
                "operation",
                "No operation specified",
                ["list_images", "list_networks", "list_volumes"],
            )

        client = _get_docker_client()
        if operation == "list_images":
            return await _list_images(all_images, filters)
        elif operation == "get_image":
            if not image:
                return _clarification_response("image", "image is required for get_image")
            return await _get_image(image)
        elif operation == "pull_image":
            if not image:
                return _clarification_response("image", "image name is required for pull_image")
            return await _pull_image(image, tag, all_images, platform)
        elif operation == "build_image":
            if not path:
                return _clarification_response(
                    "path", "path to Dockerfile context is required for build_image"
                )
            return await _build_image(
                path,
                dockerfile,
                tag,
                labels,
                buildargs,
                nocache,
                pull,
                rm,
                forcerm,
                squash,
                None,
            )
        elif operation == "remove_image":
            if not image:
                return _clarification_response(
                    "image", "image name or ID is required for remove_image"
                )
            return await _remove_image(image, force, noprune)
        elif operation == "prune_images":
            return await _prune_images(all_images, filters)
        elif operation == "list_networks":
            return await _list_networks(filters)
        elif operation == "get_network":
            if not network_id:
                return _clarification_response(
                    "network_id", "network_id is required for get_network"
                )
            return await _get_network(network_id)
        elif operation == "create_network":
            if not name:
                return _clarification_response(
                    "name", "network name is required for create_network"
                )
            return await _create_network(
                name,
                driver or "bridge",
                options,
                ipam,
                internal,
                attachable,
                ingress,
                labels,
                enable_ipv6,
            )
        elif operation == "remove_network":
            if not network_id:
                return _clarification_response(
                    "network_id", "network_id is required for remove_network"
                )
            return await _remove_network(network_id)
        elif operation == "prune_networks":
            return await _prune_networks(filters)
        elif operation == "list_volumes":
            return await _list_volumes(filters)
        elif operation == "get_volume":
            if not volume_name:
                return _clarification_response(
                    "volume_name", "volume_name is required for get_volume"
                )
            return await _get_volume(volume_name)
        elif operation == "create_volume":
            if not volume_name:
                return _clarification_response(
                    "volume_name", "volume_name is required for create_volume"
                )
            return await _create_volume(volume_name, driver or "local", driver_opts, labels)
        elif operation == "remove_volume":
            if not volume_name:
                return _clarification_response(
                    "volume_name", "volume_name is required for remove_volume"
                )
            return await _remove_volume(volume_name, force)
        elif operation == "prune_volumes":
            return await _prune_volumes(filters)
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Infrastructure operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "docker_error")


async def _list_images(
    all_images: bool = False, filters: Optional[dict[str, list[str]]] = None
) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        images = client.images.list(all=all_images, filters=filters)
        image_list = []
        for image in images:
            image_list.append(
                {
                    "id": image.id,
                    "tags": image.tags,
                    "created": image.attrs.get("Created"),
                    "size": image.attrs.get("Size", 0),
                }
            )
        return _success_response({"images": image_list, "total": len(image_list)})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _get_image(image_id: str) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        image = client.images.get(image_id)
        info = {
            "id": image.id,
            "tags": image.tags,
            "created": image.attrs.get("Created"),
            "size": image.attrs.get("Size", 0),
            "architecture": image.attrs.get("Architecture"),
            "os": image.attrs.get("Os"),
        }
        return _success_response({"image": info})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _pull_image(image_name, tag, all_tags, platform) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        if all_tags:
            client.images.pull(image_name, all_tags=True)
        else:
            image_ref = f"{image_name}:{tag}"
            client.images.pull(image_ref, platform=platform)
        return _success_response({"status": "pulled", "image": f"{image_name}:{tag}"})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _build_image(
    path, dockerfile, tag, labels, buildargs, nocache, pull, rm, forcerm, squash, network_mode
) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        build_config = {
            "path": path,
            "dockerfile": dockerfile,
            "nocache": nocache,
            "pull": pull,
            "rm": rm,
            "forcerm": forcerm,
            "squash": squash,
        }
        if tag: build_config["tag"] = tag
        if labels: build_config["labels"] = labels
        if buildargs: build_config["buildargs"] = buildargs
        if network_mode: build_config["network_mode"] = network_mode

        image, build_logs = client.images.build(**build_config)
        logs_text = "".join([log.get("stream", "") for log in build_logs if "stream" in log])
        return _success_response(
            {"image_id": image.id, "tag": tag, "build_logs": logs_text}
        )
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _remove_image(image_id, force, noprune) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        client.images.remove(image_id, force=force, noprune=noprune)
        return _success_response({"status": "removed", "image_id": image_id})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _prune_images(all_images, filters) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        result = client.images.prune(filters=filters)
        return _success_response({"pruned": result})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _list_networks(filters) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        networks = client.networks.list(filters=filters)
        network_list = [
            {
                "id": n.id,
                "name": n.name,
                "driver": n.attrs.get("Driver"),
                "scope": n.attrs.get("Scope"),
                "created": n.attrs.get("Created"),
            }
            for n in networks
        ]
        return _success_response({"networks": network_list, "total": len(network_list)})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _get_network(network_id) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        n = client.networks.get(network_id)
        info = {
            "id": n.id,
            "name": n.name,
            "driver": n.attrs.get("Driver"),
            "scope": n.attrs.get("Scope"),
            "created": n.attrs.get("Created"),
            "containers": n.attrs.get("Containers", {}),
        }
        return _success_response({"network": info})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _create_network(name, driver, options, ipam, internal, attachable, ingress, labels, enable_ipv6) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        config = {
            "name": name,
            "driver": driver,
            "internal": internal,
            "attachable": attachable,
            "ingress": ingress,
            "enable_ipv6": enable_ipv6,
        }
        if options: config["options"] = options
        if ipam: config["ipam"] = ipam
        if labels: config["labels"] = labels
        n = client.networks.create(**config)
        return _success_response({"network_id": n.id, "name": n.name})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _remove_network(network_id) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        client.networks.get(network_id).remove()
        return _success_response({"status": "removed", "network_id": network_id})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _prune_networks(filters) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        result = client.networks.prune(filters=filters)
        return _success_response({"pruned": result})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _list_volumes(filters) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        volumes = client.volumes.list(filters=filters)
        volume_list = [
            {
                "name": v.name,
                "driver": v.attrs.get("Driver"),
                "mountpoint": v.attrs.get("Mountpoint"),
                "created": v.attrs.get("CreatedAt"),
                "labels": v.attrs.get("Labels", {}),
            }
            for v in volumes
        ]
        return _success_response({"volumes": volume_list, "total": len(volume_list)})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _get_volume(volume_name) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        v = client.volumes.get(volume_name)
        info = {
            "name": v.name,
            "driver": v.attrs.get("Driver"),
            "mountpoint": v.attrs.get("Mountpoint"),
            "created": v.attrs.get("CreatedAt"),
            "labels": v.attrs.get("Labels", {}),
        }
        return _success_response({"volume": info})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _create_volume(name, driver, driver_opts, labels) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        config = {"name": name, "driver": driver}
        if driver_opts: config["driver_opts"] = driver_opts
        if labels: config["labels"] = labels
        v = client.volumes.create(**config)
        return _success_response({"volume_name": v.name, "status": "created"})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _remove_volume(volume_name, force) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        client.volumes.get(volume_name).remove(force=force)
        return _success_response({"status": "removed", "volume_name": volume_name})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _prune_volumes(filters) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        result = client.volumes.prune(filters=filters)
        return _success_response({"pruned": result})
    except Exception as e:
        return _error_response(str(e), "docker_error")
