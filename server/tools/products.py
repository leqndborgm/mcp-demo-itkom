"""Product search and advertising tools."""

import asyncio

from server.app import mcp
from server.api import qsc_search, smart_search
from server.formatters import format_qsc_results
from server.utils import time_it


@mcp.tool()
@time_it
async def find_products(query: str) -> str:
    """
    Find products in the QSC catalog based on a search query.

    INSTRUCTIONS FOR AI:
    Use this tool whenever a user asks for products or search.
    """
    result = await qsc_search({"q": query})
    return format_qsc_results(result, "compact")

@mcp.tool()
@time_it
async def explain_product(product: str) -> str:
    """Retrieve detailed information and specifications for a specific product.

    INSTRUCTIONS FOR AI:
    Use this tool whenever a user asks for detailed information about a product.
    CRITICAL: DO NOT use this tool if you need to compare or recommend between products. Use 'compare_products' instead.
    """
    result = await smart_search(product, rows=5)
    return long_format_qsc_results(result)

@mcp.tool()
@time_it
async def compare_products(product1: str, product2: str) -> str:
    """
    Compare two products directly using their names or IDs.

    MANDATORY INSTRUCTION FOR AI:
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

    combined_output = f"DETAILS PRODUCT 1:\n{text1}\n\n---\n\nDETAILS PRODUCT 2:\n{text2}"

    return combined_output


@mcp.tool()
@time_it
async def advertise_products(query: str) -> str:
    """
    Find matching accessories or upsell items.

    INSTRUCTIONS FOR AI:
    - Use only the model number or brand as the query.
    - Describe in your short description why the user might need this product.
    """

    async def get_ads(q):
        body: dict = {
            "q": q,
            "rows": 5,
        }
        return await qsc_search(body)

    result = await get_ads(query)
    docs = result.get("result", {}).get("products", {}).get("documents", [])

    # Smart Fallback: If no ads found for the full string, try shortening it
    if not docs and len(query.split()) > 2:
        result = await get_ads(" ".join(query.split()[:3]))

    return format_qsc_results(result, "advertise")
