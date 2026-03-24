"""Shared utilities: logging setup and performance decorator."""

import sys
import time
import asyncio
import logging
from functools import wraps

# Logging — always to stderr (standard for MCP servers)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-perf")


def time_it(func):
    """Decorator that logs execution time with color-coded output."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            _log_duration(func.__name__, start)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            _log_duration(func.__name__, start)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def _log_duration(name: str, start: float) -> None:
    duration = (time.perf_counter() - start) * 1000
    color = "\033[92m" if duration < 100 else "\033[93m" if duration < 500 else "\033[91m"
    reset = "\033[0m"
    logger.info(f"Tool/Function '{name}' took {color}{duration:.2f}ms{reset}")
