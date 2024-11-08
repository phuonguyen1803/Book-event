from flask import request, jsonify
from . import payment_bp
from models import mongo

@payment_bp.route("/payment/checkout", methods=["POST"])
def checkout():
    payment_info = request.get_json()
    mongo.db.payments.insert_one(payment_info)
    return jsonify({"message": "Payment processed successfully!"}), 201
