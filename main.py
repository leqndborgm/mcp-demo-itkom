"""Entrypoint — exposes the fully-registered MCP server object.

Prefect Horizon (and fastmcp inspect) discover the server via
`main.py:mcp`, so all tools, prompts, and resources must be
registered at import time.
"""

from server.app import mcp, run  # noqa: F401

# Register all tools, prompts, and resources on the mcp instance
import server.tools  # noqa: F401
import server.prompts  # noqa: F401
import server.resources  # noqa: F401

if __name__ == "__main__":
    run()
