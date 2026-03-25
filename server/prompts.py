"""MCP prompts — registered via import side-effect."""

from server.app import mcp


@mcp.prompt()
def customer_service_prompt() -> str:
    """Prompt for the customer service AI Assistant."""
    return """
"""
