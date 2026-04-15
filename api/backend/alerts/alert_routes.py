import re
from urllib.parse import urlparse, parse_qs

from flask import Blueprint, jsonify, request, current_app
from ..db_connection import get_db
from .. import ebay_client
from mysql.connector import Error

alerts = Blueprint("alerts", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ebay_url(ebay_url: str, watch_type: str):
    """
    Extract the eBay entity ID from a URL based on watch_type.

    Returns int entity_id, or raises ValueError with a descriptive message.
    """
    parsed = urlparse(ebay_url)
    path = parsed.path

    if watch_type == "listing":
        # https://www.ebay.com/itm/123456789
        # https://www.ebay.com/itm/product-name/123456789
        m = re.search(r"/itm/(?:[^/]+/)?(\d+)", path)
        if not m:
            raise ValueError("Cannot parse listing ID from URL — expected /itm/<id>")
        return int(m.group(1))

    if watch_type == "item":
        # https://www.ebay.com/b/<name>/<id>
        m = re.search(r"/b/[^/]+/(\d+)", path)
        if not m:
            raise ValueError("Cannot parse item ID from URL — expected /b/<name>/<id>")
        return int(m.group(1))

    if watch_type == "category":
        # Category ID may be in path: /b/name/12345
        # or in query params: ?sacat=12345 / ?categoryId=12345
        m = re.search(r"/b/[^/]+/(\d+)", path)
        if m:
            return int(m.group(1))
        qs = parse_qs(parsed.query)
        for key in ("sacat", "categoryId", "cat_id"):
            if key in qs:
                return int(qs[key][0])
        raise ValueError("Cannot parse category ID from URL")

    raise ValueError(f"Unknown watch_type: {watch_type}")


def _upsert_entity(cursor, watch_type: str, entity: dict):
    """Write the entity to its table using INSERT ... ON DUPLICATE KEY UPDATE."""
    if watch_type == "listing":
        cursor.execute(
            """
            INSERT INTO listings (listing_id, listing_name, url, current_price, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                listing_name  = VALUES(listing_name),
                url           = VALUES(url),
                current_price = VALUES(current_price)
            """,
            (entity["id"], entity["name"], entity["url"], entity["current_price"]),
        )
    elif watch_type == "item":
        cursor.execute(
            """
            INSERT INTO items (item_id, item_name, url, current_price, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                item_name     = VALUES(item_name),
                url           = VALUES(url),
                current_price = VALUES(current_price)
            """,
            (entity["id"], entity["name"], entity["url"], entity["current_price"]),
        )
    elif watch_type == "category":
        cursor.execute(
            """
            INSERT INTO categories (cat_id, cat_name, url, current_price, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                cat_name      = VALUES(cat_name),
                url           = VALUES(url),
                current_price = VALUES(current_price)
            """,
            (entity["id"], entity["name"], entity["url"], entity["current_price"]),
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@alerts.route("/watchlist/<int:user_id>", methods=["GET"])
def get_alerts_for_watchlist(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                a.*,
                COALESCE(l.listing_name, i.item_name, c.cat_name) AS target_name
            FROM alerts a
            JOIN watchlist w ON w.alert_id = a.alert_id
            LEFT JOIN listings   l ON a.listing_id = l.listing_id
            LEFT JOIN items      i ON a.item_id     = i.item_id
            LEFT JOIN categories c ON a.cat_id      = c.cat_id
            WHERE w.user_id = %s
            ORDER BY a.date_started DESC
            """,
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /alerts/watchlist/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@alerts.route("/<int:alert_id>", methods=["GET"])
def get_alert(alert_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                a.*,
                COALESCE(l.listing_name, i.item_name, c.cat_name) AS target_name
            FROM alerts a
            LEFT JOIN listings   l ON a.listing_id = l.listing_id
            LEFT JOIN items      i ON a.item_id     = i.item_id
            LEFT JOIN categories c ON a.cat_id      = c.cat_id
            WHERE a.alert_id = %s
            """,
            (alert_id,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Alert not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"GET /alerts/{alert_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@alerts.route("/", methods=["POST"])
def create_alert():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("watch_type", "user_id"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        watch_type = data["watch_type"]
        item_id = data.get("item_id")
        cat_id = data.get("cat_id")
        listing_id = data.get("listing_id")

        cursor.execute(
            """
            INSERT INTO alerts
                (watch_type, is_active, drop_amt, drop_percent,
                 item_id, cat_id, listing_id, original_price)
            VALUES (%s, TRUE, %s, %s, %s, %s, %s, %s)
            """,
            (
                watch_type,
                data.get("drop_amt"),
                data.get("drop_percent"),
                item_id,
                cat_id,
                listing_id,
                data.get("original_price"),
            ),
        )
        alert_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO watchlist (user_id, alert_id) VALUES (%s, %s)",
            (data["user_id"], alert_id),
        )
        db.commit()
        return jsonify({"alert_id": alert_id}), 201
    except Error as e:
        current_app.logger.error(f"POST /alerts/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@alerts.route("/from-url", methods=["POST"])
def create_alert_from_url():
    data = request.get_json()

    # Validate required fields
    for field in ("ebay_url", "watch_type", "user_id"):
        if not data or field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    ebay_url = data["ebay_url"]
    watch_type = data["watch_type"]
    user_id = data["user_id"]

    # 1. Parse entity ID from URL
    try:
        entity_id = _parse_ebay_url(ebay_url, watch_type)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # 2. Fetch entity data from eBay
    try:
        if watch_type == "listing":
            entity = ebay_client.get_listing(entity_id)
        elif watch_type == "item":
            entity = ebay_client.get_item(entity_id)
        elif watch_type == "category":
            entity = ebay_client.get_category(entity_id)
        else:
            return jsonify({"error": f"Invalid watch_type: {watch_type}"}), 400
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except (ConnectionError, RuntimeError) as e:
        current_app.logger.error(f"eBay API error in from-url: {e}")
        return jsonify({"error": "eBay API unreachable"}), 502

    # 3. Upsert entity + insert alert in one transaction
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        _upsert_entity(cursor, watch_type, entity)

        item_id = entity["id"] if watch_type == "item" else None
        cat_id = entity["id"] if watch_type == "category" else None
        listing_id = entity["id"] if watch_type == "listing" else None
        original_price = entity["current_price"]

        cursor.execute(
            """
            INSERT INTO alerts
                (watch_type, is_active, drop_amt, drop_percent,
                 item_id, cat_id, listing_id, original_price)
            VALUES (%s, TRUE, %s, %s, %s, %s, %s, %s)
            """,
            (
                watch_type,
                data.get("drop_amt"),
                data.get("drop_percent"),
                item_id,
                cat_id,
                listing_id,
                original_price,
            ),
        )
        alert_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO watchlist (user_id, alert_id) VALUES (%s, %s)",
            (user_id, alert_id),
        )
        db.commit()
    except Error as e:
        current_app.logger.error(f"POST /alerts/from-url DB error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

    return jsonify({
        "alert_id": alert_id,
        "watch_type": watch_type,
        "target_name": entity["name"],
        "original_price": original_price,
        "drop_amt": data.get("drop_amt"),
        "drop_percent": data.get("drop_percent"),
    }), 201


@alerts.route("/<int:alert_id>", methods=["PUT"])
def update_alert(alert_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        allowed = ["drop_amt", "drop_percent", "is_active"]
        fields = [f for f in allowed if data and f in data]
        if not fields:
            return jsonify({"error": "No valid fields to update"}), 400

        set_clause = ", ".join(f"{f} = %s" for f in fields)
        params = [data[f] for f in fields] + [alert_id]
        cursor.execute(f"UPDATE alerts SET {set_clause} WHERE alert_id = %s", params)
        if cursor.rowcount == 0:
            return jsonify({"error": "Alert not found"}), 404
        get_db().commit()
        return jsonify({"message": "Alert updated"}), 200
    except Error as e:
        current_app.logger.error(f"PUT /alerts/{alert_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@alerts.route("/<int:alert_id>", methods=["DELETE"])
def deactivate_alert(alert_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE alerts SET is_active = FALSE WHERE alert_id = %s", (alert_id,)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Alert not found"}), 404
        get_db().commit()
        return jsonify({"message": "Alert deactivated"}), 200
    except Error as e:
        current_app.logger.error(f"DELETE /alerts/{alert_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
