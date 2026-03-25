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
    """Decorator that logs execution time and response size (if applicable)."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = None
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            _log_stats(func.__name__, start, result)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = None
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            _log_stats(func.__name__, start, result)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def _log_stats(name: str, start: float, result: any = None) -> None:
    """Logs duration and result size (chars/tokens)."""
    duration = (time.perf_counter() - start) * 1000
    color = "\033[92m" if duration < 100 else "\033[93m" if duration < 500 else "\033[91m"
    reset = "\033[0m"

    size_info = ""
    serialized_result = None
    
    if isinstance(result, str):
        serialized_result = result
    elif isinstance(result, (dict, list)):
        try:
            import json
            serialized_result = json.dumps(result)
        except Exception:
            pass
            
    if serialized_result is not None:
        size = len(serialized_result)
        tokens = size // 4  # Standard estimation for LLMs (chars / 4)
        size_info = f" | Size: {size:,} chars (~{tokens:,} tokens)"

    logger.info(f"Tool '{name}' took {color}{duration:.2f}ms{reset}{size_info}")
