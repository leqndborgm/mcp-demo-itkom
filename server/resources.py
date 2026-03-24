"""MCP resources — registered via import side-effect."""

from server.app import mcp
from server.api import qsc_search


@mcp.resource("ressource://externdata/{query}")
async def external_api_data(query: str):
    """Get products from the external API based on a query."""
    return await qsc_search({"q": query})
