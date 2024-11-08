from bson import ObjectId
from flask import request, jsonify
from . import ticket_bp
from models import mongo

@ticket_bp.route("/ticket/add", methods=["POST"])
def add_ticket():
    ticket_info = request.get_json()
    mongo.db.tickets.insert_one(ticket_info)  # Thêm dữ liệu vé thay vì blueprint
    return jsonify({"message": "Ticket added successfully!"}), 201

@ticket_bp.route("/ticket/get/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    ticket = mongo.db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        return jsonify({"message": "Ticket not found!"}), 404
    ticket["_id"] = str(ticket["_id"])  # Chuyển ObjectId thành chuỗi
    return jsonify(ticket), 200

@ticket_bp.route("/tickets", methods=["GET"])
def get_all_tickets():
    tickets = mongo.db.tickets.find()  # Đổi db thành mongo.db
    ticket_list = []
    for ticket in tickets:
        ticket["_id"] = str(ticket["_id"])  # Chuyển ObjectId thành chuỗi
        ticket_list.append(ticket)
    return jsonify(ticket_list), 200
