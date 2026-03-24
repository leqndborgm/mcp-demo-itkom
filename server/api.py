"""Shared API client for the QSC Search API."""

import httpx

from server.config import QSC_API_URL, HTTP_TIMEOUT
from server.utils import time_it

# Shared async client with connection pooling and timeout
_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)


@time_it
async def qsc_search(body: dict) -> dict:
    """POST search request to QSC Search API.

    See qsc-admin-docs search-api-integration.
    """
    response = await _client.post(QSC_API_URL, json=body)
    response.encoding = "utf-8"
    response.raise_for_status()
    return response.json()


async def smart_search(query: str, rows: int = 1) -> dict:
    """POST search request with fallback for 0 results.

    If the initial query returns no documents and the query has more than
    3 words, it retries with only the first 3 words.
    """
    result = await qsc_search({"q": query, "rows": rows})
    docs = result.get("result", {}).get("products", {}).get("documents", [])

    if not docs and len(query.split()) > 3:
        simplified_query = " ".join(query.split()[:3])
        return await qsc_search({"q": simplified_query, "rows": rows})

    return result
