from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

watchlist = Blueprint("watchlist", __name__)


@watchlist.route("/<int:user_id>", methods=["GET"])
def get_watchlists(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM watchlist WHERE user_id = %s", (user_id,)
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"GET /watchlist/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@watchlist.route("/", methods=["POST"])
def add_alert_to_watchlist():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        for field in ("user_id", "alert_id"):
            if not data or field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """
            INSERT INTO watchlist (user_id, alert_id)
            VALUES (%s, %s)
            """,
            (data["user_id"], data["alert_id"]),
        )
        get_db().commit()
        return jsonify({"message": "Alert added to watchlist"}), 201
    except Error as e:
        current_app.logger.error(f"POST /watchlist/ error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@watchlist.route("/<int:user_id>/alerts/<int:alert_id>", methods=["DELETE"])
def remove_alert_from_watchlist(user_id, alert_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT alert_id FROM watchlist WHERE user_id = %s AND alert_id = %s",
            (user_id, alert_id),
        )
        if not cursor.fetchone():
            return jsonify({"error": "Alert not found in this watchlist"}), 404

        cursor.execute(
            "DELETE FROM watchlist WHERE user_id = %s AND alert_id = %s",
            (user_id, alert_id),
        )
        cursor.execute(
            "UPDATE alerts SET is_active = FALSE WHERE alert_id = %s", (alert_id,)
        )
        get_db().commit()
        return jsonify({"message": "Alert removed and deactivated"}), 200
    except Error as e:
        current_app.logger.error(
            f"DELETE /watchlist/{user_id}/alerts/{alert_id} error: {e}"
        )
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@watchlist.route("/<int:user_id>", methods=["DELETE"])
def delete_watchlist(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "DELETE FROM watchlist WHERE user_id = %s", (user_id,)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Watchlist not found"}), 404
        get_db().commit()
        return jsonify({"message": "Watchlist deleted"}), 200
    except Error as e:
        current_app.logger.error(f"DELETE /watchlist/{user_id} error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
