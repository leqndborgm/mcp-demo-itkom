# MCP Server

An intelligent Model Context Protocol (MCP) server for searching, comparing and explaining products. This server is optimized for LLMs (like Claude) by providing pre-formatted Markdown results directly from the backend.

## 🚀 Quickstart (Nix)

This project uses **Nix flakes** for a reproducible development environment.

1.  **Enter the environment:**
    ```bash
    nix develop
    ```
2.  **Start the server:**
    ```bash
    mcp-server
    ```
3.  **Launch the Inspector (UI) to test:**
    ```bash
    mcp-inspector
    ```
    *Alternatively, use `mcp-start` to run both at once.*

## 🛠 Features

### Product Tools
- `find_products` — Search the product catalog by keyword. Returns the top results plus further suggestions the LLM can use for follow-ups without extra API calls.
- `explain_product` — Retrieve detailed specifications for a specific product, including similar product suggestions.
- `compare_products` — Compare two products side-by-side. Fetches both in parallel for speed.

### Utility Tools
- `get_weather` — Retrieve current weather for a city or lat/lon coordinate (demo of a second-domain tool using Open-Meteo).

### Pre-formatted Markdown
The server formats all product data into clean Markdown (including image previews) before returning it to the AI — no raw JSON, consistent output every time.

### System Prompt
The server exports a `customer_service_prompt` that MCP-compatible clients can load to set the correct persona and tool-calling rules for customer service scenarios.

### Decoupled Inspector
The `mcp-inspector` tool is decoupled. While it defaults to your local server, you can use it to test *any* MCP server:
```bash
mcp-inspector node /path/to/other-server.js
```

## 🏗 Requirements
- Nix (with flakes enabled)
- Python 3.10+ (if running without Nix)

## 🐳 Deployment (HTTP/SSE)
To run the server in HTTP mode (for hosting as a web service):
```bash
python main.py http
```
The server will be available at `http://localhost:8001`.

---
*Created for Quasiris MCP Integration.*
