from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

items = Blueprint("items", __name__)


@items.route("/", methods=["GET"])
def get_all_items():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM items")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /items/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@items.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"GET /items/{item_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@items.route("/", methods=["POST"])
def upsert_item():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("item_id", "item_name", "url", "current_price"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """
            INSERT INTO items (item_id, item_name, url, current_price, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                item_name     = VALUES(item_name),
                url           = VALUES(url),
                current_price = VALUES(current_price)
            """,
            (data["item_id"], data["item_name"], data["url"], data["current_price"]),
        )
        get_db().commit()
        return jsonify({"item_id": data["item_id"]}), 201
    except Error as e:
        current_app.logger.error(f"POST /items/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
