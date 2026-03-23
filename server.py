from fastmcp import FastMCP
import requests
import os
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import FileResponse, JSONResponse
from starlette.requests import Request
# FastMCP Server with integrated UI resources

mcp = FastMCP("Test MCP Server")

def _qsc_search(body: dict) -> dict:
    """POST search request to QSC Search API. See qsc-admin-docs search-api-integration."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    response = requests.post(url, json=body)
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
    return """You are a Wago Customer Service AI. You speak via an MCP Server.
    
1. For EVERY request: Call find_suitable_products FIRST.
2. If you find products, then call advertise_products SECOND.
3. IMPORTANT: The tools return a PRE-FORMATTED Markdown list. You MUST copy this Markdown list COMPLETELY AND UNCHANGED into your response to the user. Do not summarize it. Do not leave anything out. 
4. If advertise_products returns "Keine Produkte gefunden", DO NOT tell the user that "no products were found". Simply show the products from the first tool call and leave out the advertisement.
5. If both tools find nothing after 3 tries, say: 'Question out of context.'"""

@mcp.tool(meta={"ui": {"resourceUri": "ui://products/search"}})
def find_suitable_products(query: str) -> str:
    """
    Find products in the QSC catalog based on a search query.
    
    INSTRUCTIONS FOR AI:
    Use this tool whenever a user asks for products or search. 
    You must include the results from this tool in your answer.
    """
    result = _qsc_search({"q": query})
    return format_qsc_results(result)

@mcp.tool()
def explain_product(product: str) -> str:
    """Retrieve detailed information and specifications for a specific product."""
    result = _qsc_search({"q": product, "rows": 5})
    return format_qsc_results(result)

@mcp.tool()
def get_product_by_use_case(use_case: str) -> str:
    """Identify the best products for a given application or use-case."""
    result = _qsc_search({"q": use_case, "rows": 5})
    return format_qsc_results(result)

@mcp.tool()
def compare_products(product1: str, product2: str) -> str:
    """
    Compare two products, highlighting key differences and providing an expert recommendation.
    """
    result = _qsc_search({"q": f"{product1} vs {product2}", "rows": 5})
    return format_qsc_results(result)

@mcp.tool()
def advertise_products(query: str) -> str:
    """
    Find products relevant to a query that are suitable for advertising.
    
    INSTRUCTIONS FOR AI:
    After you called find_suitable_products you will call this tool. 
    You will give a short description why the user should buy this product too. 
    If you advertise products make sure to format it nicely and make sure that the user is going to read it. You need to put the users attention to the advertised products.
    If you advertised at least one product you will end your final answer with "Erfolgreich Werbung gemacht". 
    Otherwise you will end your final answer with "Keine Werbung gemacht" and explain why you haven't done anything.
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
    result = _qsc_search(body)
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
