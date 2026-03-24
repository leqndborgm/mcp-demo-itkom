"""Configuration constants and environment variable loading."""

import os

# QSC Search API
QSC_API_URL = os.getenv(
    "QSC_API_URL",
    "https://qsc.quasiris.de/api/v1/search/ab/products",
)

# HTTP server
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("MCP_PORT", "8001"))

# HTTP client
HTTP_TIMEOUT = float(os.getenv("MCP_HTTP_TIMEOUT", "10.0"))
