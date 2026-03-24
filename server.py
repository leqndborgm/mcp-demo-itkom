from fastmcp import FastMCP
import requests
import os
import httpx
import asyncio
import sys
import time
import logging
from functools import wraps

# Set up logging to stderr (standard for MCP to see output in logs)
logging.basicConfig(level=logging.INFO, stream=sys.stderr if 'sys' in locals() else None)
logger = logging.getLogger("mcp-perf")

def time_it(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            duration = (time.perf_counter() - start) * 1000
            color = "\033[92m" if duration < 100 else "\033[93m" if duration < 500 else "\033[91m"
            reset = "\033[0m"
            logger.info(f"Tool/Function '{func.__name__}' took {color}{duration:.2f}ms{reset}")

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            duration = (time.perf_counter() - start) * 1000
            color = "\033[92m" if duration < 100 else "\033[93m" if duration < 500 else "\033[91m"
            reset = "\033[0m"
            logger.info(f"Tool/Function '{func.__name__}' took {color}{duration:.2f}ms{reset}")

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

from starlette.responses import FileResponse, RedirectResponse
import uvicorn

# FastMCP Server with integrated UI resources

mcp = FastMCP("Test MCP Server")

@time_it
async def _qsc_search(body: dict) -> dict:
    """POST search request to QSC Search API. See qsc-admin-docs search-api-integration."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body)
    response.encoding = 'utf-8'
    response.raise_for_status()
    return response.json()

@mcp.resource("ressource://externdata/{query}")
async def external_api_data(query: str):
    """Get products from the external API based on a query."""
    return await _qsc_search({"q": query})

async def smart_search(query: str, rows: int = 1):
    """POST search request to QSC Search API with fallback for 0 results."""
    result = await _qsc_search({"q": query, "rows": rows})
    docs = result.get("result", {}).get("products", {}).get("documents", [])
    
    if not docs and len(query.split()) > 2:
        simplified_query = " ".join(query.split()[:3])
        return await _qsc_search({"q": simplified_query, "rows": rows})
        
    return result

@mcp.prompt()
def customer_service_prompt() -> str:
    """System prompt for the customer service AI Assistant."""
    return """You are a Customer Service AI. You speak via an MCP Server.

### MANDATORY STEP-BY-STEP WORKFLOW:
1. PHASE 1 (DISCOVERY): Identify products. Call ONE of: find_suitable_products, explain_product, or compare_products.
2. PHASE 2 (ADVERTISING): ALWAYS call 'advertise_products' using the names/IDs found in Phase 1. This step is NOT OPTIONAL.
3. PHASE 3 (RESPONSE): Combine all tool results 100% EXACTLY into your final message.

### FORMATTING RULES:
- CRITICAL: Tools (find_suitable_products, explain_product, compare_products, advertise_products) provide READY-FORMATTED Markdown and HTML.
- You MUST NOT CHANGE ANYTHING in these tool outputs (no rephrasing, no summarization).
- If advertise_products returns "Keine Produkte gefunden", simply omit that part in your final message without mentioning it.
- When comparing, provide your own summary/recommendation ONLY AFTER displaying the raw tool blocks.

### EXAMPLE OF A PERFECT RESPONSE SEQUENCE:
User: "I am looking for NYY 3x2,5 ground cable."
AI: [Calls find_suitable_products]
AI: [Calls advertise_products]
Assistant: [Outputs both results exactly]
"""

@mcp.tool()
@time_it
async def find_suitable_products(query: str) -> str:
    """
    Find products in the QSC catalog based on a search query.
    
    INSTRUCTIONS FOR AI:
    Use this tool whenever a user asks for products or search. 
    You must include the results from this tool in your answer.
    """
    result = await _qsc_search({"q": query})
    return format_qsc_results(result)

@mcp.tool()
@time_it
async def explain_product(product: str) -> str:
    """Retrieve detailed information and specifications for a specific product.
    
    INSTRUCTIONS FOR AI:
    Use this tool whenever a user asks for detailed information about a product. 
    CRITICAL: DO NOT use this tool if you need to compare or recommend between products. Use 'compare_products' instead.
    """
    result = await smart_search(product, rows=5)
    return format_qsc_results(result)

@mcp.tool()
@time_it
async def get_product_by_use_case(use_case: str) -> str:
    """Identify the best products for a given application or use-case."""
    result = await smart_search(use_case, rows=5)
    return format_qsc_results(result)

@mcp.tool()
@time_it
async def compare_products(product1: str, product2: str) -> str:
    """
    Compare two products directly using their names or IDs.

    MANDATORY INSTRUCTION FOR AI:
    - You MUST clean the input strings: Extract ONLY the core brand and model number (e.g., 'Hauff EKD25').
    - NEVER include descriptive phrases like 'für Gebäude' or 'im Koffer' in the parameters.
    - BAD EXAMPLE: 'Baier BDN453 Diamantfräse im Koffer' -> GOOD EXAMPLE: 'Baier BDN453'
    - This is critical because the search engine will return 0 results for long descriptive strings.
    Use this tool ONLY when a user explicitly wants to compare two specific products or asks for a recommendation between two options. 
    Do NOT call explain_product twice; 
    Use this tool instead to get a unified and correctly formatted comparison output. 
    This tool retrieves information for both products in parallel, making it faster and more suitable for direct comparisons than individual lookups.
    """
    res1_task = smart_search(product1, rows=1)
    res2_task = smart_search(product2, rows=1)

    res1, res2 = await asyncio.gather(res1_task, res2_task)

    text1 = format_qsc_results(res1)
    text2 = format_qsc_results(res2)
    
    text1 = text1.replace("\n\n**ERFOLGREICH**", "")
    text2 = text2.replace("\n\n**ERFOLGREICH**", "")
    
    combined_output = f"DETAILS PRODUCT 1:\n{text1}\n\n---\n\nDETAILS PRODUCT 2:\n{text2}"
    
    return combined_output

@mcp.tool()
@time_it
async def advertise_products(query: str) -> str:
    """
    Find matching accessories or upsell items (type 'ast').
    
    INSTRUCTIONS FOR AI:
    - MANDATORY: Call this tool SECOND after you have used any product tool (find, explain or compare).
    - Use only the model number or brand as the query.
    """
    async def get_ads(q):
        body: dict = {
            "q": q,
            "rows": 5,
            "filters": {
                "type": {
                    "filterType": "term",
                    "values": ["ast"],
                }
            },
        }
        return await _qsc_search(body)

    result = await get_ads(query)
    docs = result.get("result", {}).get("products", {}).get("documents", [])
    
    # Smart Fallback: If no ads found for the full string, try shortening it
    if not docs and len(query.split()) > 2:
        result = await get_ads(" ".join(query.split()[:3]))
        
    return format_qsc_results(result)


def format_qsc_results(result: dict) -> str:
    formatted_results = ""
    documents = result.get("result", {}).get("products", {}).get("documents", [])
    
    if not documents:
        return "Keine Produkte gefunden.\n\n**ERFOLGREICH**"
        
    for item in documents:
        product_doc = item.get("document", {})
        
        name = product_doc.get("name", product_doc.get("title", "Kein Name"))
        product_id = item.get("id", "Keine ID")
        position = item.get("position", item.get("pos", ""))
        description = product_doc.get("description", "Keine Beschreibung")
        
        category_raw = product_doc.get("category", "PRODUKT")
        if isinstance(category_raw, list) and category_raw:
            category_raw = category_raw[0]
        category_header = f"**{str(category_raw).upper()}**"
        
        # Image link logic
        image = product_doc.get("publicPreviewImageUrl", 
                               product_doc.get("privatePreviewImageUrl", 
                               product_doc.get("imageUrl", "")))
        
        # Build block
        formatted_results += f"{category_header}\n"
        formatted_results += f"* **Name:** {name}\n"
        formatted_results += f"* **Produkt-ID:** {product_id}\n"
        if position:
            formatted_results += f"* **Position:** {position}\n"
        formatted_results += f"* **Beschreibung:** {description}\n"
        if image:
            formatted_results += f"![Produktbild]({image})\n"
        formatted_results += "\n---\n\n"
    
    return formatted_results.strip() + "\n\n**ERFOLGREICH**"



@mcp.tool()
def get_weather(location: str):
    """Retrieve current weather data for a location. Provide a city name (e.g. 'Berlin', 'London') or 'latitude,longitude' (e.g. '52.52,13.41'). Uses the Open-Meteo public API."""
    location = location.strip()
    # Check if input is lat,long
    if "," in location and len(location.split(",")) == 2:
        try:
            lat, lon = location.split(",")
            lat, lon = float(lat.strip()), float(lon.strip())
        except ValueError:
            lat, lon = _geocode_location(location)
    else:
        lat, lon = _geocode_location(location)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
        "timezone": "auto",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def _geocode_location(location: str) -> tuple[float, float]:
    """Resolve city name to latitude and longitude using Open-Meteo Geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": location, "count": 1}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    if not results:
        raise ValueError(f"Location not found: {location}")
    return results[0]["latitude"], results[0]["longitude"]




if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Get the standard MCP HTTP app
        app = mcp.http_app()
        
        # Restore index.html serving
        @app.route("/")
        @app.route("/index.html")
        async def serve_index(request):
            return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

        # Add /mcp as an alias for /sse (Standard SSE endpoint of FastMCP)
        @app.route("/mcp")
        async def mcp_redirect(request):
            return RedirectResponse(url="/sse")

        print("🚀 Starting MCP Server in HTTP mode on http://localhost:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        # Default to STDIO transport
        mcp.run()
