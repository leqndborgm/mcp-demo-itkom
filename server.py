from fastmcp import FastMCP

import json
import requests

mcp = FastMCP("Test MCP Server")

@mcp.resource("ressource://externdata/{query}")
def external_api_data(query: str):
    """Get products from the external API based on a query."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    params = {"q": query}
    response = requests.get(url, params=params)
    response.encoding = 'utf-8'  # Ensure it's read as UTF-8 if server headers are missing
    response.raise_for_status()   # ensures errors are visible
    return response.json()

@mcp.tool()
def find_suitable_products(query: str):
    """Find suitable products based on the query."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    params = {"q": query}
    response = requests.get(url, params=params)
    response.encoding = 'utf-8'
    response.raise_for_status()  
    return response.json()

@mcp.tool()
def explain_product(product: str):
    """Explain a product and return the differences."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    params = {"q": product, "limit": 5}
    response = requests.get(url, params=params)
    response.encoding = 'utf-8'
    response.raise_for_status()   
    return response.json()

@mcp.tool()
def get_product_by_use_case(use_case: str):
    """Get a suitable product by use case."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    params = {"q": use_case, "limit": 5}
    response = requests.get(url, params=params)
    response.encoding = 'utf-8'
    response.raise_for_status()   
    return response.json()

@mcp.tool()
def compare_products(product1: str, product2: str):
    """Compare two products and return the differences. Give your honest opinion about what product is better and why. Make sure that everything is formatted nicely"""
    # Search for product1 as the primary query for comparison
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    params = {"q": f"{product1} vs {product2}", "limit": 5}
    response = requests.get(url, params=params)
    response.encoding = 'utf-8'
    response.raise_for_status()  
    return response.json()

@mcp.tool()
def advertise_products(query: str):
    """Find products that could be relevant to the query and can be advertised. They will be shown after the suitable products and marked as 'Das könnte dich auch interessieren:' They should be also different than the suitable products (e.g. suitable product is a mouse, more suitable products are keyboards, monitors, etc.)."""
    url = "https://qsc.quasiris.de/api/v1/search/ab/products"
    params = {"q": query, "limit": 5}
    response = requests.get(url, params=params)
    response.encoding = 'utf-8'
    response.raise_for_status()  
    return response.json()    

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)

