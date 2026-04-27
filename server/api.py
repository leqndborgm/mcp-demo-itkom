"""Shared API client for the QSC Search API."""

import httpx
import hashlib, json
import logging

from cachetools import TTLCache

from server.config import QSC_API_URL, QSC_RESULT_KEY, HTTP_TIMEOUT
from server.utils import time_it, logger

# Shared async client with connection pooling and timeout
_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)

_cache = TTLCache(maxsize=512, ttl=300)

@time_it
async def qsc_search(body: dict) -> dict:
    """POST search request to QSC Search API.

    """
    cache_key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    if cache_key in _cache:
        logger.info(f"Cache hit for key: {cache_key}")
        return _cache[cache_key]        
    
    logger.info(f"Cache miss for key: {cache_key}")
    response = await _client.post(QSC_API_URL, json=body)
    response.encoding = "utf-8"
    response.raise_for_status()
    result = response.json()
    _cache[cache_key] = result
    return result


def build_search_body(
    query: str,
    rows: int = 10,
) -> dict:
    """Build a QSC search request body."""
    return {"q": query, "rows": rows}


async def smart_search(
    query: str,
    rows: int = 1,
) -> dict:
    """POST search request with fallback for 0 results.

    If the initial query returns no documents and the query has more than
    2 words, it retries with only the first 2 words.
    """
    body = build_search_body(query, rows)
    result = await qsc_search(body)
    docs = get_documents(result)

    if not docs and len(query.split()) > 2:
        simplified_query = " ".join(query.split()[:2])
        fallback_body = build_search_body(simplified_query, rows)
        return await qsc_search(fallback_body)

    return result


def get_documents(result: dict) -> list:
    """Extract documents from a QSC search response, regardless of result key."""
    return result.get("result", {}).get(QSC_RESULT_KEY, {}).get("documents", [])
