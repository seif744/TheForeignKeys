from flask import Blueprint, jsonify, request, current_app
from backend import ebay_client

ebay = Blueprint("ebay", __name__)


@ebay.route("/listing", methods=["GET"])
def get_listing():
    listing_id = request.args.get("listing_id", type=int)
    if not listing_id:
        return jsonify({"error": "Missing required query parameter: listing_id"}), 400
    try:
        return jsonify(ebay_client.get_listing(listing_id)), 200
    except (ConnectionError, RuntimeError) as e:
        current_app.logger.error(f"GET /ebay/listing error: {e}")
        return jsonify({"error": "eBay API unreachable"}), 502


@ebay.route("/item", methods=["GET"])
def get_item():
    item_id = request.args.get("item_id", type=int)
    if not item_id:
        return jsonify({"error": "Missing required query parameter: item_id"}), 400
    try:
        return jsonify(ebay_client.get_item(item_id)), 200
    except (ConnectionError, RuntimeError) as e:
        current_app.logger.error(f"GET /ebay/item error: {e}")
        return jsonify({"error": "eBay API unreachable"}), 502


@ebay.route("/category", methods=["GET"])
def get_category():
    cat_id = request.args.get("cat_id", type=int)
    if not cat_id:
        return jsonify({"error": "Missing required query parameter: cat_id"}), 400
    try:
        return jsonify(ebay_client.get_category(cat_id)), 200
    except (ConnectionError, RuntimeError) as e:
        current_app.logger.error(f"GET /ebay/category error: {e}")
        return jsonify({"error": "eBay API unreachable"}), 502