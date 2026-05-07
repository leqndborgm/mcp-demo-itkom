"""FastMCP application instance and HTTP/STDIO startup logic."""

import os
import sys
import logging

from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager

from server.config import SERVER_HOST, SERVER_PORT
from server.api import qsc_search

# ── MCP instance (imported by tools, prompts, resources for registration) ──
mcp = FastMCP("BauMax Einkaufsberater")


def _register_all() -> None:
    """Import side-effect modules to register tools, prompts, and resources."""
    import server.tools  # noqa: F401
    import server.prompts  # noqa: F401
    import server.resources  # noqa: F401

async def warmup():
    """Pre-warm HTTP connection pool"""
    try: 
        await qsc_search({"q": "warmup", "rows": 1})
    except Exception:
        pass


def create_http_app():
    """Build the Starlette ASGI app with MCP + static routes."""
    from starlette.routing import Route

    _register_all()
    app = mcp.http_app()

    # Chain our warmup with FastMCP's own lifespa
    _fastmcp_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def combined_lifespan(scope):
        async with _fastmcp_lifespan(scope):
            await warmup()
            logging.info("Warmup complete")
            yield

    app.router.lifespan_context = combined_lifespan

    async def serve_index(request):
        return FileResponse(os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html"))

    async def merkzettel_api(request):
        from server.state import merkzettel_lists
        active = {name: items for name, items in merkzettel_lists.items() if items}
        return JSONResponse({
            "lists": active,
            "total_items": sum(len(v) for v in active.values()),
        })

    # Prepend custom routes (before MCP's catch-all routes)
    app.routes.insert(0, Route("/", serve_index))
    app.routes.insert(1, Route("/index.html", serve_index))
    app.routes.insert(2, Route("/api/merkzettel", merkzettel_api))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

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
