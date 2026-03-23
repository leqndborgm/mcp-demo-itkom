from fastmcp import FastMCP
import requests
import os
import httpx

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import FileResponse, JSONResponse
from starlette.requests import Request
# FastMCP Server with integrated UI resources

mcp = FastMCP("Test MCP Server")

async def _qsc_search(body: dict) -> dict:
    """POST search request to QSC Search API. See qsc-admin-docs search-api-integration."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body)
    response.encoding = 'utf-8'
    response.raise_for_status()
    return response.json()

@mcp.resource("ressource://externdata/{query}")
def external_api_data(query: str):
    """Get products from the external API based on a query."""
    return _qsc_search({"q": query})

@mcp.prompt()
def customer_service_prompt() -> str:
    """System prompt for the customer service AI Assistant."""
    return """You are a Customer Service AI. You speak via an MCP Server.
    
1. For EVERY request: Call find_suitable_products FIRST.
2. If you find products, then call advertise_products SECOND.
3. CRITICAL: Tools (`find_suitable_products`, `advertise_products`) provide READY-FORMATTED Markdown and HTML (including `<br>` and `<b>` tags).
   You MUST NOT CHANGE ANYTHING in these tool outputs! 
   This includes:
   - NO rephrasing of sentences.
   - NO summarization of details.
   - NEVER delete HTML tags like <br> or <b>.
   Copy the tool results 100% EXACTLY into your final response.
   Treat the tool output as a "final text block" that you only "pass through" to the user.
4. If advertise_products returns "Keine Produkte gefunden", DO NOT tell the user that "no products were found". Simply show the products from the first tool call and leave out the advertisement.
5. If both tools find nothing after 3 tries, say: 'Question out of context.'
6. When comparing products, first display the detailed blocks for both products provided by the tool, and then provide your summary/comparison below them.
### EXAMPLE OF A PERFECT RESPONSE:
User: "I am looking for NYY 3x2,5 ground cable."
AI: [Calls find_suitable_products]
Assistant: **ERDKABEL NYY / NYKY / NYZG2Y / NYYÖ**
* **Name:** NYY-J 3x2,5 qmm RE 500m-Trommel PVC-isoliertes Erd-Kabel
* **Produkt-ID:** 515c9433-1c7b-47df-b144-025ec072f228
* **Beschreibung:** "Erdkabel NYY-J/NYY-O<br />nach VDE 0276<br /><b>Anwendung:</b><br />..."
--- 
**ERFOLGREICH**
"""

@mcp.tool(meta={"ui": {"resourceUri": "ui://products/search"}})
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
async def explain_product(product: str) -> str:
    """Retrieve detailed information and specifications for a specific product."""
    result =await _qsc_search({"q": product, "rows": 5})
    return format_qsc_results(result)

@mcp.tool()
async def get_product_by_use_case(use_case: str) -> str:
    """Identify the best products for a given application or use-case."""
    result = await _qsc_search({"q": use_case, "rows": 5})
    return format_qsc_results(result)

@mcp.tool()
async def compare_products(product1: str, product2: str) -> str:
    """
    Compare two products by retrieving their details individually.
    """
    res1 = _qsc_search({"q": product1, "rows": 1})
    res2 = _qsc_search({"q": product2, "rows": 1})
    
    res1, res2 = await asyncio.gather(res1, res2)

    text1 = format_qsc_results(res1)
    text2 = format_qsc_results(res2)
    
    text1 = text1.replace("\n\n**ERFOLGREICH**", "")
    text2 = text2.replace("\n\n**ERFOLGREICH**", "")
    
    combined_output = f"DETAILS PRODUCT 1:\n{text1}\n\n---\n\nDETAILS PRODUCT 2:\n{text2}"
    
    return combined_output

@mcp.tool()
async def advertise_products(query: str) -> str:
    """
    Find products relevant to a query that are suitable for advertising.
    
    INSTRUCTIONS FOR AI:
    After you called find_suitable_products you will call this tool. 
    You will give a short description why the user should buy this product too. 
    If you advertise products make sure to format it nicely and make sure that the user is going to read it. You need to put the users attention to the advertised products.
    """
    body: dict = {
        "q": query,
        "rows": 5,
        "filters": {
            "type": {
                "filterType": "term",
                "values": ["ats"],
            }
        },
    }
    result = await _qsc_search(body)
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



@mcp.tool(meta={"ui": {"resourceUri": "ui://weather/view"}})
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


# Register UI resources using standard MCP decorators
@mcp.resource("ui://products/search", mime_type="text/html")
def products_search_ui():
    """UI for product search."""
    return """
<div style="font-family: sans-serif; padding: 20px; background: #0a0f1d; color: #e2e8f0; border-radius: 8px;">
    <h2 style="color: #6366f1;">Product Search</h2>
    <div id="results">Search results will appear here.</div>
</div>
"""

@mcp.resource("ui://weather/view", mime_type="text/html")
def weather_view_ui():
    """UI for weather report."""
    return """
<div style="font-family: sans-serif; padding: 20px; background: #1e293b; color: #f8fafc; border-radius: 8px;">
    <h2 style="color: #38bdf8;">Weather Report</h2>
</div>
"""

# Simple Tool Rendering (Dashboard)
async def serve_index(request: Request):
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

async def list_tools_api(request: Request):
    tools = await mcp.get_tools()
    return JSONResponse([
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.to_mcp_tool().inputSchema,
            "meta": t.meta if hasattr(t, "meta") else {}
        } for t in tools.values()
    ])

async def get_resource_api(request: Request):
    uri = request.query_params.get("uri")
    if not uri:
        return JSONResponse({"error": "URI required"}, status_code=400)
    try:
        resource = None
        for res_name, res_obj in mcp._resources.items():
            if res_obj.uri == uri:
                content = res_obj.func()
                import asyncio
                if asyncio.iscoroutine(content):
                    content = await content
                return JSONResponse({"resource": content})
        
        return JSONResponse({"error": f"Resource not found: {uri}"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def call_tool_api(request: Request):
    name = request.path_params["name"]
    try:
        args = await request.json()
        tool = await mcp.get_tool(name)
        result = tool.func(**args)
        import asyncio
        if asyncio.iscoroutine(result):
            result = await result
        return JSONResponse({"result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import sys
    # If 'http' is passed as an argument, run as HTTP/SSE server (for local dashboard/inspector)
    # Otherwise, run as STDIO server (default for platforms like Prefect Horizon)
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        import uvicorn
        # Get the Starlette app from FastMCP
        app = mcp.http_app()
        
        # Add our dashboard routes directly to it
        app.add_route("/", serve_index, methods=["GET"])
        app.add_route("/index.html", serve_index, methods=["GET"])
        app.add_route("/api/tools", list_tools_api, methods=["GET"])
        app.add_route("/api/resource", get_resource_api, methods=["GET"])
        app.add_route("/api/call/{name}", call_tool_api, methods=["POST"])

        print("🚀 Starting MCP Server in HTTP mode on http://localhost:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        # Default to STDIO transport
        mcp.run()
