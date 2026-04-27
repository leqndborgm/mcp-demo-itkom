"""MCP prompts — registered via import side-effect."""

from server.app import mcp


@mcp.prompt()
def customer_service_prompt() -> str:
    """Prompt for the customer service AI Assistant."""
    return """
WICHTIG: ANTWORTE IMMER AUF DEUTSCH. SELBST WENN DER NUTZER IN EINER ANDEREN SPRACHE SCHREIBT, DANN ANTWORTEST DU TROTZDEM AUF DEUTSCH
"""
