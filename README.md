# MCP Server

An intelligent Model Context Protocol (MCP) server for searching, comparing and advertising products. This server is optimized for LLMs (like Claude) by providing pre-formatted Markdown results directly from the backend.

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

### Product Search & Tools
- `find_suitable_products`: Main search functionality for the catalog.
- `explain_product`: Detailed specifications for a chosen product.
- `compare_products`: Expert comparison between two products.
- `advertise_products`: Finds products suitable for marketing campaigns (filtered by type: `ats`).
- `get_product_by_use_case`: Use-case based recommendations.

### Pre-formatted Markdown
The server doesn't just return raw JSON. It formats all product data into beautiful, user-ready Markdown (including **BOLD CAPS** categories and image previews) before handing it to the AI. This guarantees a consistent UI experience.

### System Prompt
The server exports a dedicated `customer_service_prompt`. When using an MCP-compatible client, you can load this prompt to instantly set the correct persona and tool-calling rules for the customer service.

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
python server.py http
```
The server will be available at `http://localhost:8001`.

---
*Created for Quasiris MCP Integration.*
