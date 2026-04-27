"""Import all tool modules to trigger registration on the MCP instance.

To add a new tool:
  1. Create a new file in this directory (e.g. my_tool.py)
  2. Import and register tools using `from server.app import mcp` + `@mcp.tool()`
  3. Add `from server.tools import my_tool` below
"""

from server.tools import products  # noqa: F401
