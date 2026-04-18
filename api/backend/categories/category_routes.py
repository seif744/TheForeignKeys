from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

categories = Blueprint("categories", __name__)


@categories.route("/", methods=["GET"])
def get_all_categories():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM categories")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /categories/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@categories.route("/<int:cat_id>", methods=["GET"])
def get_category(cat_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM categories WHERE cat_id = %s", (cat_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Category not found"}), 404
        return jsonify(row), 200
    except Error as e:
        current_app.logger.error(f"GET /categories/{cat_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@categories.route("/", methods=["POST"])
def upsert_category():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("cat_id", "cat_name", "url", "current_price"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """
            INSERT INTO categories (cat_id, cat_name, url, current_price, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                cat_name      = VALUES(cat_name),
                url           = VALUES(url),
                current_price = VALUES(current_price)
            """,
            (data["cat_id"], data["cat_name"], data["url"], data["current_price"]),
        )
        get_db().commit()
        return jsonify({"cat_id": data["cat_id"]}), 201
    except Error as e:
        current_app.logger.error(f"POST /categories/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
