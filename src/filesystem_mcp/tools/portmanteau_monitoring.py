import logging
from datetime import datetime
from typing import Any, Literal, Optional

import psutil

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
async def monitor_ops(
    operation: Literal[
        "get_system_status",
        "get_resource_usage",
        "get_process_info",
        "get_performance_metrics",
        "get_memory_info",
        "get_cpu_info",
        "get_disk_usage",
        "get_network_info",
    ],
    include_processes: bool = False,
    include_disk: bool = True,
    include_network: bool = True,
    max_processes: int = 10,
    filter_pattern: Optional[str] = None,
    sort_by: str = "cpu_percent",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """Real-time System Monitoring (Metrics, Resources, Processes).

    Args:
        operation (Literal, required): Available monitoring operations:
            - "get_system_status": Comprehensive snapshot of health
            - "get_resource_usage": Quick CPU/RAM/Disk summary
            - "get_process_info": List running processes with filters
            - "get_performance_metrics": High-res usage stats
            - "get_memory_info": Detailed RAM/Swap breakdown
            - "get_cpu_info": Core counts, frequency, and times
            - "get_disk_usage": Partition sizes and free space
            - "get_network_info": Interface addresses and counters

        --- OPTIONS ---

        include_processes/disk/network (bool): Toggle status detail levels
        max_processes (int): Limit process list size. Default: 10
        filter_pattern (str | None): Keyword search for processes
        sort_by (str): Sort field (cpu_percent, memory_percent, name)
        sort_order (str): "asc" or "desc". Default: "desc"
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["get_system_status", "get_resource_usage"]
            )

        if operation == "get_system_status":
            return await _get_system_status(
                include_processes, include_disk, include_network, max_processes
            )
        elif operation == "get_resource_usage":
            return await _get_resource_usage()
        elif operation == "get_process_info":
            return await _get_process_info(max_processes, filter_pattern, sort_by, sort_order)
        elif operation == "get_performance_metrics":
            return await _get_performance_metrics()
        elif operation == "get_memory_info":
            return await _get_memory_info()
        elif operation == "get_cpu_info":
            return await _get_cpu_info()
        elif operation == "get_disk_usage":
            return await _get_disk_usage()
        elif operation == "get_network_info":
            return await _get_network_info()
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Monitoring operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _get_system_status(proc, disk, net, max_p):
    try:
        import platform

        res = {
            "timestamp": datetime.now().isoformat(),
            "system": platform.system(),
            "release": platform.release(),
            "cpu_count": psutil.cpu_count(),
            "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory()._asdict(),
        }
        if disk:
            res["disk"] = psutil.disk_usage("/")._asdict()
        if proc:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                procs.append(p.info)
            res["processes"] = sorted(
                procs, key=lambda x: x.get("cpu_percent", 0), reverse=True
            )[:max_p]
        if net:
            res["network"] = psutil.net_io_counters()._asdict()

        return _success_response(res, related_operations=["get_resource_usage", "get_process_info"])
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_resource_usage():
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


async def _get_process_info(limit, pattern, sort, order):
    try:
        procs = []
        for p in psutil.process_iter(
            ["pid", "name", "username", "status", "cpu_percent", "memory_percent"]
        ):
            try:
                if pattern and pattern.lower() not in p.info["name"].lower():
                    continue
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda x: x.get(sort, 0) or 0, reverse=(order == "desc"))
        return _success_response({"processes": procs[:limit], "total_matching": len(procs)})
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_performance_metrics():
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


async def _get_memory_info():
    try:
        return _success_response(
            {"virtual": psutil.virtual_memory()._asdict(), "swap": psutil.swap_memory()._asdict()}
        )
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_cpu_info():
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


async def _get_disk_usage():
    try:
        partitions = []
        for p in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(p.mountpoint)._asdict()
                partitions.append({"device": p.device, "mountpoint": p.mountpoint, "usage": usage})
            except (PermissionError, OSError):
                continue
        return _success_response({"partitions": partitions})
    except Exception as e:
        return _error_response(str(e), "psutil_error")


async def _get_network_info():
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
