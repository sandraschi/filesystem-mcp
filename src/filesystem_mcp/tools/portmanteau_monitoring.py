"""System monitoring tools — one tool per view (CPU, memory, processes, etc.)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import psutil

from .utils import _error_response, _get_app, _success_response

logger = logging.getLogger(__name__)

async def _get_system_status(
    include_processes: bool,
    include_disk: bool,
    include_network: bool,
    max_processes: int,
) -> dict[str, Any]:
    try:
        import platform

        res: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "system": platform.system(),
            "release": platform.release(),
            "cpu_count": psutil.cpu_count(),
            "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory()._asdict(),
        }
        if include_disk:
            res["disk"] = psutil.disk_usage("/")._asdict()
        if include_processes:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                procs.append(p.info)
            res["processes"] = sorted(
                procs, key=lambda x: x.get("cpu_percent", 0), reverse=True
            )[:max_processes]
        if include_network:
            res["network"] = psutil.net_io_counters()._asdict()

        return _success_response(
            res,
            related_operations=[
                "monitor_get_resource_usage",
                "monitor_get_process_info",
            ],
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_resource_usage() -> dict[str, Any]:
    try:
        return _success_response(
            {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage("/")._asdict(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_process_info(
    limit: int,
    pattern: str | None,
    sort: str,
    order: str,
) -> dict[str, Any]:
    try:
        procs = []
        for p in psutil.process_iter(
            ["pid", "name", "username", "status", "cpu_percent", "memory_percent"]
        ):
            try:
                if pattern and pattern.lower() not in (p.info.get("name") or "").lower():
                    continue
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(
            key=lambda x: x.get(sort, 0) or 0,
            reverse=(order == "desc"),
        )
        return _success_response({"processes": procs[:limit], "total_matching": len(procs)})
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_performance_metrics() -> dict[str, Any]:
    try:
        return _success_response(
            {
                "cpu_times": psutil.cpu_times_percent(interval=0.1)._asdict(),
                "virtual_memory": psutil.virtual_memory()._asdict(),
                "swap_memory": psutil.swap_memory()._asdict(),
                "disk_io": psutil.disk_io_counters()._asdict(),
                "net_io": psutil.net_io_counters()._asdict(),
            }
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_memory_info() -> dict[str, Any]:
    try:
        return _success_response(
            {
                "virtual": psutil.virtual_memory()._asdict(),
                "swap": psutil.swap_memory()._asdict(),
            }
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_cpu_info() -> dict[str, Any]:
    try:
        return _success_response(
            {
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "usage_per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
            }
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_disk_usage() -> dict[str, Any]:
    try:
        partitions = []
        for p in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(p.mountpoint)._asdict()
                partitions.append(
                    {"device": p.device, "mountpoint": p.mountpoint, "usage": usage}
                )
            except (PermissionError, OSError):
                continue
        return _success_response({"partitions": partitions})
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_network_info() -> dict[str, Any]:
    try:
        return _success_response(
            {
                "io_counters": psutil.net_io_counters()._asdict(),
                "addresses": {
                    k: [a._asdict() for a in v] for k, v in psutil.net_if_addrs().items()
                },
                "stats": {k: v._asdict() for k, v in psutil.net_if_stats().items()},
            }
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


_app = _get_app()


@_app.tool()
async def monitor_get_system_status(
    include_processes: bool = False,
    include_disk: bool = True,
    include_network: bool = True,
    max_processes: int = 10,
) -> dict[str, Any]:
    """Snapshot of OS, CPU count, load, memory, optional disk/network and top processes.

    Recovery: If psutil raises AccessDenied, retry with fewer options or run with appropriate permissions.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: timestamp, system, release, cpu_count, cpu_usage_percent, memory (dict),
        optional disk, processes, network — structure matches psutil named tuples as dicts.
    """
    try:
        return await _get_system_status(
            include_processes, include_disk, include_network, max_processes
        )
    except Exception as e:
        logger.exception("monitor_get_system_status failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_resource_usage() -> dict[str, Any]:
    """CPU, memory, root disk usage, and boot time.

    Idempotency: Read-only; safe to retry.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: cpu_percent, memory, disk, boot_time (ISO string).
    """
    try:
        return await _get_resource_usage()
    except Exception as e:
        logger.exception("monitor_get_resource_usage failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_process_info(
    max_processes: int = 10,
    filter_pattern: str | None = None,
    sort_by: str = "cpu_percent",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """List running processes with optional substring filter on the process name.

    Args:
        filter_pattern: Case-insensitive substring matched against process **name** (not regex).
            Example: \"python\" matches \"python.exe\". Omit to include all accessible processes.
        sort_by: One of cpu_percent, memory_percent, name (falls back to 0 if missing).
        sort_order: \"asc\" or \"desc\".

    Recovery: AccessDenied on some PIDs is normal; total_matching reflects filtered list.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {\"processes\": [dict], \"total_matching\": int}
    """
    try:
        return await _get_process_info(max_processes, filter_pattern, sort_by, sort_order)
    except Exception as e:
        logger.exception("monitor_get_process_info failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_performance_metrics() -> dict[str, Any]:
    """Detailed CPU times, memory, swap, disk I/O, and network I/O counters.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: cpu_times, virtual_memory, swap_memory, disk_io, net_io (dicts).
    """
    try:
        return await _get_performance_metrics()
    except Exception as e:
        logger.exception("monitor_get_performance_metrics failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_memory_info() -> dict[str, Any]:
    """Virtual and swap memory breakdown.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: virtual, swap (dicts from psutil).
    """
    try:
        return await _get_memory_info()
    except Exception as e:
        logger.exception("monitor_get_memory_info failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_cpu_info() -> dict[str, Any]:
    """Core counts, optional frequency, and per-CPU usage.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: physical_cores, total_cores, frequency (dict | None), usage_per_cpu (list).
    """
    try:
        return await _get_cpu_info()
    except Exception as e:
        logger.exception("monitor_get_cpu_info failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_disk_usage() -> dict[str, Any]:
    """Per-partition usage (skips mounts that raise PermissionError).

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: {\"partitions\": [{\"device\", \"mountpoint\", \"usage\"}, ...]}
    """
    try:
        return await _get_disk_usage()
    except Exception as e:
        logger.exception("monitor_get_disk_usage failed")
        return _error_response(str(e), "internal_error")


@_app.tool()
async def monitor_get_network_info() -> dict[str, Any]:
    """Aggregate I/O counters and per-interface addresses and stats.

    Returns:
        dict: success, operation, result (payload), timestamp, next_steps, related_operations.
        result: io_counters, addresses, stats.
    """
    try:
        return await _get_network_info()
    except Exception as e:
        logger.exception("monitor_get_network_info failed")
        return _error_response(str(e), "internal_error")
