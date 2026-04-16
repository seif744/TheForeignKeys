"""
API helper module for BargainHunters.

All backend communication lives here. Pages import these functions and
receive plain Python dicts/lists — no requests logic needed in pages.

On any HTTP or connection error, functions return None (for single objects)
or an empty list (for collections) so pages can handle failure gracefully.

Usage:
    from modules.api import get_users, create_alert_from_url, ...
"""

import logging
import requests

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:4000"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get(path: str, params: dict = None):
    """GET request. Returns parsed JSON or None on failure."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error("GET %s failed: %s", path, e)
        return None


def _post(path: str, payload: dict):
    """POST request. Returns parsed JSON or None on failure."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error("POST %s failed: %s", path, e)
        return None


def _put(path: str, payload: dict):
    """PUT request. Returns parsed JSON or None on failure."""
    try:
        r = requests.put(f"{API_BASE}{path}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error("PUT %s failed: %s", path, e)
        return None


def _delete(path: str):
    """DELETE request. Returns parsed JSON or None on failure."""
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error("DELETE %s failed: %s", path, e)
        return None


# ---------------------------------------------------------------------------
# Users  —  /u
# ---------------------------------------------------------------------------

def get_users() -> list:
    """Return all active users."""
    return _get("/u/") or []


def get_user(user_id: int) -> dict | None:
    """Return a single user by ID."""
    return _get(f"/u/{user_id}")


def create_user(name: str, email: str) -> dict | None:
    """
    Create a new user.
    Returns: {"user_id": int}
    """
    return _post("/u/", {"name": name, "email": email})


def update_user(user_id: int, name: str = None, email: str = None) -> dict | None:
    """Update a user's name and/or email."""
    payload = {}
    if name is not None:
        payload["name"] = name
    if email is not None:
        payload["email"] = email
    return _put(f"/u/{user_id}", payload)


def delete_user(user_id: int) -> dict | None:
    """Soft-delete (deactivate) a user."""
    return _delete(f"/u/{user_id}")


# ---------------------------------------------------------------------------
# Alerts  —  /alerts
# ---------------------------------------------------------------------------

def get_alerts_for_user(user_id: int) -> list:
    """
    Return all alerts in a user's watchlist.
    Each alert includes target_name (listing/item/category name).
    """
    return _get(f"/alerts/watchlist/{user_id}") or []


def get_alert(alert_id: int) -> dict | None:
    """Return a single alert with its target name."""
    return _get(f"/alerts/{alert_id}")


def create_alert_from_url(
    ebay_url: str,
    watch_type: str,
    user_id: int,
    drop_amt: float = None,
    drop_percent: float = None,
) -> dict | None:
    """
    Create an alert by supplying an eBay URL.
    The backend parses the URL, fetches current price via SerpAPI,
    upserts the entity, and creates the alert in one step.

    watch_type: "listing" | "item" | "category"
    Returns: {alert_id, watch_type, target_name, original_price, drop_amt, drop_percent}
    """
    payload = {
        "ebay_url": ebay_url,
        "watch_type": watch_type,
        "user_id": user_id,
    }
    if drop_amt is not None:
        payload["drop_amt"] = drop_amt
    if drop_percent is not None:
        payload["drop_percent"] = drop_percent
    return _post("/alerts/from-url", payload)


def create_alert(
    watch_type: str,
    user_id: int,
    item_id: int = None,
    cat_id: int = None,
    listing_id: int = None,
    drop_amt: float = None,
    drop_percent: float = None,
    original_price: float = None,
) -> dict | None:
    """
    Create an alert manually (without a URL).
    Returns: {"alert_id": int}
    """
    payload = {"watch_type": watch_type, "user_id": user_id}
    if item_id is not None:
        payload["item_id"] = item_id
    if cat_id is not None:
        payload["cat_id"] = cat_id
    if listing_id is not None:
        payload["listing_id"] = listing_id
    if drop_amt is not None:
        payload["drop_amt"] = drop_amt
    if drop_percent is not None:
        payload["drop_percent"] = drop_percent
    if original_price is not None:
        payload["original_price"] = original_price
    return _post("/alerts/", payload)


def update_alert(
    alert_id: int,
    drop_amt: float = None,
    drop_percent: float = None,
    is_active: bool = None,
) -> dict | None:
    """Update an alert's thresholds or active status."""
    payload = {}
    if drop_amt is not None:
        payload["drop_amt"] = drop_amt
    if drop_percent is not None:
        payload["drop_percent"] = drop_percent
    if is_active is not None:
        payload["is_active"] = is_active
    return _put(f"/alerts/{alert_id}", payload)


def deactivate_alert(alert_id: int) -> dict | None:
    """Deactivate (soft-delete) an alert."""
    return _delete(f"/alerts/{alert_id}")


# ---------------------------------------------------------------------------
# Watchlist  —  /watchlist
# ---------------------------------------------------------------------------

def get_watchlist(user_id: int) -> list:
    """Return all watchlist entries for a user."""
    return _get(f"/watchlist/{user_id}") or []


def add_to_watchlist(user_id: int, alert_id: int) -> dict | None:
    """Link an existing alert to a user's watchlist."""
    return _post("/watchlist/", {"user_id": user_id, "alert_id": alert_id})


def remove_from_watchlist(user_id: int, alert_id: int) -> dict | None:
    """Remove one alert from a user's watchlist and deactivate it."""
    return _delete(f"/watchlist/{user_id}/alerts/{alert_id}")


def clear_watchlist(user_id: int) -> dict | None:
    """Delete a user's entire watchlist."""
    return _delete(f"/watchlist/{user_id}")


# ---------------------------------------------------------------------------
# Notifications  —  /notifications
# ---------------------------------------------------------------------------

def get_notifications(user_id: int) -> list:
    """Return all notifications for a user, newest first."""
    return _get(f"/notifications/{user_id}") or []


def create_notification(content: str, user_id: int, alert_id: int) -> dict | None:
    """
    Create a notification tied to an alert.
    Returns: {"notification_id": int}
    """
    return _post("/notifications/", {
        "content": content,
        "user_id": user_id,
        "alert_id": alert_id,
    })


# ---------------------------------------------------------------------------
# Listings  —  /listings
# ---------------------------------------------------------------------------

def get_listings() -> list:
    """Return all listings."""
    return _get("/listings/") or []


def get_listing(listing_id: int) -> dict | None:
    """Return a single listing by ID."""
    return _get(f"/listings/{listing_id}")


# ---------------------------------------------------------------------------
# Items  —  /items
# ---------------------------------------------------------------------------

def get_items() -> list:
    """Return all items."""
    return _get("/items/") or []


def get_item(item_id: int) -> dict | None:
    """Return a single item by ID."""
    return _get(f"/items/{item_id}")


# ---------------------------------------------------------------------------
# Categories  —  /categories
# ---------------------------------------------------------------------------

def get_categories() -> list:
    """Return all categories."""
    return _get("/categories/") or []


def get_category(cat_id: int) -> dict | None:
    """Return a single category by ID."""
    return _get(f"/categories/{cat_id}")


# ---------------------------------------------------------------------------
# Feedback  —  /feedback
# ---------------------------------------------------------------------------

def get_feedback() -> list:
    """Return all feedback entries, newest first."""
    return _get("/feedback/") or []


def submit_feedback(content: str, user_id: int) -> dict | None:
    """
    Submit user feedback.
    Returns: {"feedback_id": int}
    """
    return _post("/feedback/", {"content": content, "user_id": user_id})


# ---------------------------------------------------------------------------
# Errors  —  /errors
# ---------------------------------------------------------------------------

def get_errors() -> list:
    """Return all logged errors."""
    return _get("/errors/") or []


def get_errors_for_user(user_id: int) -> list:
    """Return all errors logged for a specific user."""
    return _get(f"/errors/user/{user_id}") or []


def log_error(error_desc: str, user_id: int) -> dict | None:
    """
    Log an application error for a user.
    Returns: {"error_id": int}
    """
    return _post("/errors/", {"error_desc": error_desc, "user_id": user_id})
