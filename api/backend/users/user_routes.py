from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

users = Blueprint("users", __name__)


@users.route("/", methods=["GET"])
def get_all_users():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE is_active = TRUE")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /u/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@users.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user), 200
    except Error as e:
        current_app.logger.error(f"GET /u/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@users.route("/", methods=["POST"])
def create_user():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("name", "email"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            (data["name"], data["email"]),
        )
        get_db().commit()
        return jsonify({"user_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"POST /u/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@users.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        allowed = ["name", "email"]
        fields = [f for f in allowed if data and f in data]
        if not fields:
            return jsonify({"error": "No valid fields to update"}), 400

        set_clause = ", ".join(f"{f} = %s" for f in fields)
        params = [data[f] for f in fields] + [user_id]
        cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = %s", params)
        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404
        get_db().commit()
        return jsonify({"message": "User updated"}), 200
    except Error as e:
        current_app.logger.error(f"PUT /u/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@users.route("/<int:user_id>", methods=["DELETE"])
def deactivate_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE users SET is_active = FALSE WHERE user_id = %s", (user_id,)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404
        get_db().commit()
        return jsonify({"message": "User deactivated"}), 200
    except Error as e:
        current_app.logger.error(f"DELETE /u/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
