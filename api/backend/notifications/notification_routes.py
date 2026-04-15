from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

notifications = Blueprint("notifications", __name__)


@notifications.route("/<int:user_id>", methods=["GET"])
def get_notifications(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY sent_date DESC",
            (user_id,),
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /notifications/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@notifications.route("/", methods=["POST"])
def create_notification():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("content", "user_id", "alert_id"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            "INSERT INTO notifications (content, user_id, alert_id) VALUES (%s, %s, %s)",
            (data["content"], data["user_id"], data["alert_id"]),
        )
        get_db().commit()
        return jsonify({"notification_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"POST /notifications/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
