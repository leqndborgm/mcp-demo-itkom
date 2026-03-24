"""FastMCP application instance and HTTP/STDIO startup logic."""

import os
import sys

from fastmcp import FastMCP
from starlette.responses import FileResponse, RedirectResponse

from server.config import SERVER_HOST, SERVER_PORT

# ── MCP instance (imported by tools, prompts, resources for registration) ──
mcp = FastMCP("Test MCP Server")


def _register_all() -> None:
    """Import side-effect modules to register tools, prompts, and resources."""
    import server.tools  # noqa: F401
    import server.prompts  # noqa: F401
    import server.resources  # noqa: F401


def create_http_app():
    """Build the Starlette ASGI app with MCP + static routes."""
    from starlette.routing import Route

    _register_all()
    app = mcp.http_app()

    async def serve_index(request):
        return FileResponse(os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html"))

    async def mcp_redirect(request):
        return RedirectResponse(url="/sse")

    # Prepend custom routes (before MCP's catch-all routes)
    app.routes.insert(0, Route("/", serve_index))
    app.routes.insert(1, Route("/index.html", serve_index))
    app.routes.insert(2, Route("/mcp", mcp_redirect))

    return app


def run() -> None:
    """Entry point: choose STDIO or HTTP transport based on CLI args."""
    _register_all()

    if len(sys.argv) > 1 and sys.argv[1] == "http":
        import uvicorn

        app = create_http_app()
        print(f"🚀 Starting MCP Server in HTTP mode on http://localhost:{SERVER_PORT}")
        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
    else:
        # Default to STDIO transport
        mcp.run()
