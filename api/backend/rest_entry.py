from flask import Flask
from dotenv import load_dotenv
import os
import logging

from backend.db_connection import init_app as init_db
from backend.users.user_routes import users
from backend.watchlist.watchlist_routes import watchlist
from backend.alerts.alert_routes import alerts
from backend.notifications.notification_routes import notifications
from backend.listings.listing_routes import listings
from backend.items.item_routes import items
from backend.categories.category_routes import categories
from backend.feedback.feedback_routes import feedback
from backend.errors.error_routes import errors


def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('API startup')

    load_dotenv()

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(users,         url_prefix="/u")
    app.register_blueprint(watchlist,     url_prefix="/watchlist")
    app.register_blueprint(alerts,        url_prefix="/alerts")
    app.register_blueprint(notifications, url_prefix="/notifications")
    app.register_blueprint(listings,      url_prefix="/listings")
    app.register_blueprint(items,         url_prefix="/items")
    app.register_blueprint(categories,    url_prefix="/categories")
    app.register_blueprint(feedback,      url_prefix="/feedback")
    app.register_blueprint(errors,        url_prefix="/errors")

    return app
