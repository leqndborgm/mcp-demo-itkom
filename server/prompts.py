"""MCP prompts — registered via import side-effect."""

from server.app import mcp


@mcp.prompt()
def customer_service_prompt() -> str:
    """Minimal MCP context — formatting and persona are defined in the agent config system prompt."""
    return """
WICHTIG: Antworte immer auf Deutsch — egal in welcher Sprache der Nutzer schreibt.
"""
