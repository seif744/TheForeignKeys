from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

listings = Blueprint("listings", __name__)


@listings.route("/", methods=["GET"])
def get_all_listings():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM listings")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /listings/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@listings.route("/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM listings WHERE listing_id = %s", (listing_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Listing not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"GET /listings/{listing_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@listings.route("/", methods=["POST"])
def upsert_listing():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("listing_id", "listing_name", "url", "current_price"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """
            INSERT INTO listings (listing_id, listing_name, url, current_price, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                listing_name  = VALUES(listing_name),
                url           = VALUES(url),
                current_price = VALUES(current_price)
            """,
            (data["listing_id"], data["listing_name"], data["url"], data["current_price"]),
        )
        get_db().commit()
        return jsonify({"listing_id": data["listing_id"]}), 201
    except Error as e:
        current_app.logger.error(f"POST /listings/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
