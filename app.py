from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

app = Flask(__name__)

# --- MongoDB connection ---
client = MongoClient("mongodb://localhost:27017/")
db = client["stocksense"]

suppliers = db["suppliers"]
products = db["products"]
receipts = db["receipts"]
stock = db["stock"]


def serialize(doc):
    """Convert Mongo's ObjectId to a plain string for JSON responses."""
    doc["_id"] = str(doc["_id"])
    return doc


# ---------------- SUPPLIER ROUTES ----------------

@app.route("/suppliers", methods=["POST"])
def create_supplier():
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    supplier = {
        "name": data["name"],
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "address": data.get("address", ""),
    }
    result = suppliers.insert_one(supplier)
    supplier["_id"] = str(result.inserted_id)
    return jsonify(supplier), 201


@app.route("/suppliers", methods=["GET"])
def list_suppliers():
    all_suppliers = [serialize(s) for s in suppliers.find()]
    return jsonify(all_suppliers), 200


@app.route("/suppliers/<supplier_id>", methods=["GET"])
def get_supplier(supplier_id):
    try:
        supplier = suppliers.find_one({"_id": ObjectId(supplier_id)})
    except InvalidId:
        return jsonify({"error": "invalid supplier id"}), 400

    if not supplier:
        return jsonify({"error": "supplier not found"}), 404
    return jsonify(serialize(supplier)), 200


# ---------------- PRODUCT ROUTES ----------------

@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()

    if not data or not data.get("name") or not data.get("sku"):
        return jsonify({"error": "name and sku are required"}), 400

    if products.find_one({"sku": data["sku"]}):
        return jsonify({"error": "sku already exists"}), 400

    product = {
        "name": data["name"],
        "sku": data["sku"],
        "uom": data.get("uom", "unit"),
    }
    result = products.insert_one(product)
    product["_id"] = str(result.inserted_id)
    return jsonify(product), 201


@app.route("/products", methods=["GET"])
def list_products():
    all_products = [serialize(p) for p in products.find()]
    return jsonify(all_products), 200


@app.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    try:
        product = products.find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        return jsonify({"error": "invalid product id"}), 400

    if not product:
        return jsonify({"error": "product not found"}), 404
    return jsonify(serialize(product)), 200


# ---------------- RECEIPT ROUTES ----------------

@app.route("/receipts", methods=["POST"])
def create_receipt():
    data = request.get_json()

    if not data or not data.get("supplier_id") or not data.get("lines"):
        return jsonify({"error": "supplier_id and lines are required"}), 400

    # validate supplier exists
    try:
        supplier = suppliers.find_one({"_id": ObjectId(data["supplier_id"])})
    except InvalidId:
        return jsonify({"error": "invalid supplier_id"}), 400
    if not supplier:
        return jsonify({"error": "supplier not found"}), 404

    # validate each line: product exists and quantity is positive
    clean_lines = []
    for line in data["lines"]:
        product_id = line.get("product_id")
        quantity = line.get("quantity")

        if not product_id or quantity is None or quantity <= 0:
            return jsonify({"error": "each line needs product_id and a positive quantity"}), 400

        try:
            product = products.find_one({"_id": ObjectId(product_id)})
        except InvalidId:
            return jsonify({"error": f"invalid product_id: {product_id}"}), 400
        if not product:
            return jsonify({"error": f"product not found: {product_id}"}), 404

        clean_lines.append({"product_id": product_id, "quantity": quantity})

    receipt = {
        "supplier_id": data["supplier_id"],
        "date": datetime.utcnow().isoformat(),
        "status": "draft",
        "lines": clean_lines,
    }
    result = receipts.insert_one(receipt)
    receipt["_id"] = str(result.inserted_id)
    return jsonify(receipt), 201


@app.route("/receipts", methods=["GET"])
def list_receipts():
    """Receipt history — all receipts, newest first."""
    all_receipts = [serialize(r) for r in receipts.find().sort("date", -1)]
    return jsonify(all_receipts), 200


@app.route("/receipts/<receipt_id>", methods=["GET"])
def get_receipt(receipt_id):
    try:
        receipt = receipts.find_one({"_id": ObjectId(receipt_id)})
    except InvalidId:
        return jsonify({"error": "invalid receipt id"}), 400

    if not receipt:
        return jsonify({"error": "receipt not found"}), 404
    return jsonify(serialize(receipt)), 200


@app.route("/receipts/<receipt_id>/validate", methods=["POST"])
def validate_receipt(receipt_id):
    try:
        receipt = receipts.find_one({"_id": ObjectId(receipt_id)})
    except InvalidId:
        return jsonify({"error": "invalid receipt id"}), 400

    if not receipt:
        return jsonify({"error": "receipt not found"}), 404

    if receipt["status"] == "validated":
        return jsonify({"error": "receipt already validated"}), 400

    # increase stock for each line
    for line in receipt["lines"]:
        stock.update_one(
            {"product_id": line["product_id"]},
            {"$inc": {"quantity": line["quantity"]}},
            upsert=True,
        )

    receipts.update_one(
        {"_id": ObjectId(receipt_id)},
        {"$set": {"status": "validated", "validated_date": datetime.utcnow().isoformat()}},
    )

    updated_receipt = receipts.find_one({"_id": ObjectId(receipt_id)})
    return jsonify(serialize(updated_receipt)), 200


# ---------------- STOCK ROUTES ----------------

@app.route("/stock", methods=["GET"])
def list_stock():
    all_stock = [serialize(s) for s in stock.find()]
    return jsonify(all_stock), 200


@app.route("/stock/<product_id>", methods=["GET"])
def get_stock(product_id):
    entry = stock.find_one({"product_id": product_id})
    if not entry:
        return jsonify({"product_id": product_id, "quantity": 0}), 200
    return jsonify(serialize(entry)), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
