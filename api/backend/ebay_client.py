"""
Thin wrapper around the SerpAPI eBay endpoints.

Environment variables required:
  SERPAPI_KEY — API key from https://serpapi.com

No OAuth needed — SerpAPI handles eBay authentication internally.
All functions return a uniform dict:
    {"id": int, "name": str, "url": str, "current_price": float}
"""
import os
import requests

SERPAPI_BASE = "https://serpapi.com/search"


def _api_key() -> str:
    key = os.getenv("SERPAPI_KEY")
    if not key:
        raise RuntimeError("SERPAPI_KEY must be set in environment")
    return key


def _get(params: dict) -> dict:
    """Shared GET helper — raises ConnectionError on bad HTTP status."""
    resp = requests.get(SERPAPI_BASE, params=params, timeout=10)
    if not resp.ok:
        raise ConnectionError(f"SerpAPI error: {resp.status_code} {resp.text}")
    return resp.json()


def get_listing(listing_id: int) -> dict:
    """
    Fetch a single eBay listing by legacy item number.

    eBay item numbers are globally unique so the first organic result
    is always the exact listing.

    Returns:
        {"id": int, "name": str, "url": str, "current_price": float, "in_stock": bool}
        in_stock is False (with price 0.0 and empty name/url) when no active listings are found.
    Raises:
        ConnectionError on HTTP errors.
    """
    data = _get({
        "engine": "ebay",
        "api_key": _api_key(),
        "_nkw": str(listing_id),
    })

    results = data.get("organic_results", [])
    if not results:
        return {"id": listing_id, "name": "", "url": "", "current_price": 0.0, "in_stock": False}

    best = results[0]
    price = float((best.get("price") or {}).get("extracted") or 0)
    return {
        "id": listing_id,
        "name": best.get("title", ""),
        "url": best.get("link", ""),
        "current_price": price,
        "in_stock": True,
    }


def get_item(item_id: int) -> dict:
    """
    Fetch eBay product listings by EPID and return the lowest-priced result.

    Returns:
        {"id": int, "name": str, "url": str, "current_price": float, "in_stock": bool}
        in_stock is False (with price 0.0 and empty name/url) when no active listings are found.
    Raises:
        ConnectionError on HTTP errors.
    """
    data = _get({
        "engine": "ebay_product",
        "api_key": _api_key(),
        "_epid": str(item_id),
    })

    results = data.get("organic_results", [])
    if not results:
        return {"id": item_id, "name": "", "url": "", "current_price": 0.0, "in_stock": False}

    best = results[0]
    price = float((best.get("price") or {}).get("extracted") or 0)
    return {
        "id": item_id,
        "name": best.get("title", ""),
        "url": best.get("link", ""),
        "current_price": price,
        "in_stock": True,
    }


def search(query: str, limit: int = 12) -> list:
    """
    Search eBay by keyword and return up to `limit` results.

    Returns a list of:
        {"id": str, "name": str, "url": str, "current_price": float, "thumbnail": str}
    """
    data = _get({
        "engine": "ebay",
        "api_key": _api_key(),
        "_nkw": query,
    })

    results = (data or {}).get("organic_results", [])
    output = []
    for r in results[:limit]:
        output.append({
            "id": r.get("item_id", ""),
            "name": r.get("title", ""),
            "url": r.get("link", ""),
            "current_price": float((r.get("price") or {}).get("extracted") or 0),
            "thumbnail": r.get("thumbnail", ""),
        })
    return output


def get_category(cat_id: int) -> dict:
    """
    Search eBay for the cheapest listing in a given category.

    Uses _sop=15 (sort by lowest price + shipping).

    Returns:
        {"id": int, "name": str, "url": str, "current_price": float, "in_stock": bool}
        in_stock is False (with price 0.0) when no active listings are found in this category.
    Raises:
        ConnectionError on HTTP errors.
    """
    data = _get({
        "engine": "ebay",
        "api_key": _api_key(),
        "_sacat": str(cat_id),
        "_sop": "15",   # lowest price + shipping first
    })

    results = data.get("organic_results", [])
    if not results:
        return {"id": cat_id, "name": f"Category {cat_id}", "url": "", "current_price": 0.0, "in_stock": False}

    best = results[0]
    price = float((best.get("price") or {}).get("extracted") or 0)

    # SerpAPI may include a category name in search_information
    cat_name = (
        data.get("search_information", {}).get("category_name")
        or f"Category {cat_id}"
    )
    return {
        "id": cat_id,
        "name": cat_name,
        "url": best.get("link", ""),
        "current_price": price,
        "in_stock": True,
    }
