from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

feedback = Blueprint("feedback", __name__)


@feedback.route("/", methods=["GET"])
def get_all_feedback():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /feedback/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@feedback.route("/", methods=["POST"])
def submit_feedback():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("content", "user_id"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            "INSERT INTO feedback (content, user_id) VALUES (%s, %s)",
            (data["content"], data["user_id"]),
        )
        get_db().commit()
        return jsonify({"feedback_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"POST /feedback/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
