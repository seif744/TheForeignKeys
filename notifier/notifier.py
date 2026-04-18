"""
BargainHunters Notification Service

Runs every hour. For each active alert, fetches the current eBay price and
triggers a notification (DB row + email) if the condition is met. After
triggering, the alert is deactivated so it only fires once.
"""
import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText

import requests
import mysql.connector
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("MYSQL_ROOT_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

SMTP_HOST     = os.getenv("SMTP_HOST")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 465))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

API_BASE = os.getenv("API_BASE", "http://web-api:4000")


def _fetch_entity(watch_type: str, entity_id: int) -> dict:
    """Call the Flask /ebay endpoint and return the entity dict.

    Raises ConnectionError on non-200 responses.
    """
    route_map = {
        "listing":  ("listing",  "listing_id"),
        "item":     ("item",     "item_id"),
        "category": ("category", "cat_id"),
    }
    path, param = route_map[watch_type]
    resp = requests.get(f"{API_BASE}/ebay/{path}", params={param: entity_id}, timeout=10)
    if not resp.ok:
        raise ConnectionError(f"API error {resp.status_code} for {watch_type} {entity_id}: {resp.text}")
    return resp.json()


def _send_email(to_address: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = to_address
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_address, msg.as_string())


def _notify(
    conn,
    cursor,
    alert_id: int,
    user_id: int,
    user_email: str,
    user_name: str,
    entity: dict,
    trigger_reason: str,
) -> None:
    """Insert a notification row, deactivate the alert, then send the email."""
    content = (
        f"Hi {user_name},\n\n"
        f"Your BargainHunters alert has been triggered!\n\n"
        f"{trigger_reason}\n\n"
        f"View on eBay: {entity['url']}\n\n"
        f"— The BargainHunters Team"
    )
    cursor.execute(
        "INSERT INTO notifications (content, user_id, alert_id) VALUES (%s, %s, %s)",
        (content, user_id, alert_id),
    )
    cursor.execute(
        "UPDATE alerts SET is_active = FALSE, date_ended = %s WHERE alert_id = %s",
        (datetime.utcnow(), alert_id),
    )
    conn.commit()
    _send_email(user_email, f"BargainHunters: Price Alert for {entity['name']}", content)
    logger.info(f"Notified user {user_id} for alert {alert_id} ({entity['name']})")


def check_alerts() -> None:
    logger.info("Starting alert check run.")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                a.alert_id, a.watch_type,
                a.drop_amt, a.drop_percent, a.original_price,
                a.item_id, a.cat_id, a.listing_id,
                w.user_id,
                u.email AS user_email,
                u.name  AS user_name
            FROM alerts     a
            JOIN watchlist  w ON w.alert_id = a.alert_id
            JOIN users      u ON u.user_id  = w.user_id
            WHERE a.is_active = TRUE AND a.date_ended IS NULL
            """
        )
        alerts = cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to query alerts: {e}")
        cursor.close()
        conn.close()
        return

    logger.info(f"Found {len(alerts)} active alert(s) to check.")

    for alert in alerts:
        alert_id       = alert["alert_id"]
        watch_type     = alert["watch_type"]
        original_price = float(alert["original_price"] or 0)
        drop_amt       = float(alert["drop_amt"])     if alert["drop_amt"]     is not None else None
        drop_percent   = float(alert["drop_percent"]) if alert["drop_percent"] is not None else None
        user_id        = alert["user_id"]
        user_email     = alert["user_email"]
        user_name      = alert["user_name"]

        # Fetch current price via the Flask /ebay API
        entity_id_map = {
            "listing":  alert["listing_id"],
            "item":     alert["item_id"],
            "category": alert["cat_id"],
        }
        if watch_type not in entity_id_map:
            logger.warning(f"Unknown watch_type '{watch_type}' on alert {alert_id}, skipping.")
            continue

        try:
            entity = _fetch_entity(watch_type, entity_id_map[watch_type])
        except (ConnectionError, RuntimeError) as e:
            logger.warning(f"eBay API error for alert {alert_id}: {e}")
            continue

        current_price = entity["current_price"]
        in_stock      = entity["in_stock"]
        entity_name   = entity["name"] or f"{watch_type} {alert_id}"

        # Evaluate trigger condition
        triggered      = False
        trigger_reason = ""

        if drop_amt is None and drop_percent is None:
            # In-stock alert — fires when the target comes back in stock
            if in_stock:
                triggered = True
                trigger_reason = f"'{entity_name}' is back in stock at ${current_price:.2f}."

        elif drop_amt is not None:
            if in_stock and current_price <= original_price - drop_amt:
                triggered = True
                trigger_reason = (
                    f"'{entity_name}' dropped by ${drop_amt:.2f}. "
                    f"Current price: ${current_price:.2f} (was ${original_price:.2f})."
                )

        else:
            # drop_percent alert
            threshold = original_price * (1 - drop_percent / 100)
            if in_stock and current_price <= threshold:
                triggered = True
                trigger_reason = (
                    f"'{entity_name}' dropped by {drop_percent:.1f}%. "
                    f"Current price: ${current_price:.2f} (was ${original_price:.2f})."
                )

        if not triggered:
            logger.debug(
                f"Alert {alert_id} not triggered "
                f"(current=${current_price:.2f}, original=${original_price:.2f})."
            )
            continue

        try:
            _notify(conn, cursor, alert_id, user_id, user_email, user_name, entity, trigger_reason)
        except Exception as e:
            logger.error(f"Failed to notify for alert {alert_id}: {e}")

    cursor.close()
    conn.close()
    logger.info("Alert check run complete.")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(check_alerts, "interval", hours=1)
    logger.info("Notifier service started — checking alerts every hour.")
    check_alerts()  # run once immediately on startup
    scheduler.start()