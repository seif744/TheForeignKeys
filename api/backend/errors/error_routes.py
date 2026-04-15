from flask import Blueprint, jsonify, request, current_app
from ..db_connection import get_db
from mysql.connector import Error

errors = Blueprint("errors", __name__)


@errors.route("/", methods=["GET"])
def get_all_errors():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM errors")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /errors/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@errors.route("/user/<int:user_id>", methods=["GET"])
def get_errors_for_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM errors WHERE user_id = %s", (user_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /errors/user/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@errors.route("/", methods=["POST"])
def log_error():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("error_desc", "user_id"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            "INSERT INTO errors (error_desc, user_id) VALUES (%s, %s)",
            (data["error_desc"], data["user_id"]),
        )
        get_db().commit()
        return jsonify({"error_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"POST /errors/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
