"""
Thin wrapper around the eBay Browse API.

Environment variables required:
  EBAY_APP_ID   — OAuth client_id  (also called AppID)
  EBAY_CERT_ID  — OAuth client_secret (also called CertID)

Tokens are fetched with the Client Credentials grant and cached in memory
until they expire. Thread safety is not a concern for the dev/course setup.
"""
import os
import time
import base64
import requests

_token_cache = {"access_token": None, "expires_at": 0}

EBAY_API_BASE = "https://api.ebay.com"
EBAY_TOKEN_URL = f"{EBAY_API_BASE}/identity/v1/oauth2/token"
EBAY_BROWSE_BASE = f"{EBAY_API_BASE}/buy/browse/v1"
EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"


def _get_access_token():
    if time.time() < _token_cache["expires_at"] - 30:
        return _token_cache["access_token"]

    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")
    if not app_id or not cert_id:
        raise RuntimeError("EBAY_APP_ID and EBAY_CERT_ID must be set")

    credentials = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
    resp = requests.post(
        EBAY_TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": EBAY_SCOPE},
        timeout=10,
    )
    if not resp.ok:
        raise ConnectionError(f"eBay token request failed: {resp.status_code} {resp.text}")

    body = resp.json()
    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"] = time.time() + int(body.get("expires_in", 7200))
    return _token_cache["access_token"]


def _auth_headers():
    return {"Authorization": f"Bearer {_get_access_token()}"}


def get_listing(listing_id: int) -> dict:
    """
    Fetch a single eBay listing (by legacyItemId).

    Returns:
        {"id": int, "name": str, "url": str, "current_price": float}
    Raises:
        LookupError if eBay returns 404.
        ConnectionError on non-recoverable HTTP errors.
    """
    item_id_str = f"v1|{listing_id}|0"
    resp = requests.get(
        f"{EBAY_BROWSE_BASE}/item/{item_id_str}",
        headers=_auth_headers(),
        timeout=10,
    )
    if resp.status_code == 404:
        raise LookupError(f"eBay listing {listing_id} not found")
    if not resp.ok:
        raise ConnectionError(f"eBay API error: {resp.status_code} {resp.text}")

    data = resp.json()
    price = float(data.get("price", {}).get("value", 0))
    return {
        "id": listing_id,
        "name": data.get("title", ""),
        "url": data.get("itemWebUrl", ""),
        "current_price": price,
    }


def get_item(item_id: int) -> dict:
    """
    Search eBay for listings matching an EPID and return the lowest price.

    Returns:
        {"id": int, "name": str, "url": str, "current_price": float}
    """
    resp = requests.get(
        f"{EBAY_BROWSE_BASE}/item_summary/search",
        headers=_auth_headers(),
        params={"epid": str(item_id), "limit": 50, "sort": "price"},
        timeout=10,
    )
    if not resp.ok:
        raise ConnectionError(f"eBay API error: {resp.status_code} {resp.text}")

    summaries = resp.json().get("itemSummaries", [])
    if not summaries:
        raise LookupError(f"No eBay listings found for item/EPID {item_id}")

    best = summaries[0]
    price = float(best.get("price", {}).get("value", 0))
    return {
        "id": item_id,
        "name": best.get("title", ""),
        "url": best.get("itemWebUrl", ""),
        "current_price": price,
    }


def get_category(cat_id: int) -> dict:
    """
    Search eBay for the cheapest listing in a category.

    Returns:
        {"id": int, "name": str, "url": str, "current_price": float}
    """
    resp = requests.get(
        f"{EBAY_BROWSE_BASE}/item_summary/search",
        headers=_auth_headers(),
        params={"category_ids": str(cat_id), "limit": 50, "sort": "price"},
        timeout=10,
    )
    if not resp.ok:
        raise ConnectionError(f"eBay API error: {resp.status_code} {resp.text}")

    data = resp.json()
    summaries = data.get("itemSummaries", [])
    if not summaries:
        raise LookupError(f"No eBay listings found for category {cat_id}")

    best = summaries[0]
    price = float(best.get("price", {}).get("value", 0))
    cat_name = (
        data.get("refinement", {})
        .get("dominantCategoryAspects", [{}])[0]
        .get("localizedAspectName", f"Category {cat_id}")
    )
    return {
        "id": cat_id,
        "name": cat_name,
        "url": best.get("itemWebUrl", ""),
        "current_price": price,
    }
