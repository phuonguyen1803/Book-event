from bson import ObjectId
from flask import request, jsonify, render_template, Blueprint
from flask_pymongo import PyMongo

# Tạo blueprint cho ghế
seat_bp = Blueprint('seat', __name__)
mongo = None  # Đặt mongo thành None ban đầu

def init_app(app):
    global mongo
    mongo = PyMongo(app)

@seat_bp.route("/seat/add", methods=["POST"])
def add_seat():
    seat_info = request.get_json()
    mongo.db.seats.insert_one(seat_info)
    return jsonify({"message": "Seat added successfully!"}), 201

@seat_bp.route("/seat/get/<seat_id>", methods=["GET"])
def get_seat(seat_id):
    seat = mongo.db.seats.find_one({"_id": ObjectId(seat_id)})
    if not seat:
        return jsonify({"message": "Seat not found!"}), 404
    seat["_id"] = str(seat["_id"])  # Chuyển ObjectId thành chuỗi
    return jsonify(seat), 200

@seat_bp.route("/seats", methods=["GET"])
def get_all_seats():
    seats = mongo.db.seats.find()
    seat_list = []
    for seat in seats:
        seat["_id"] = str(seat["_id"])  # Chuyển ObjectId thành chuỗi
        seat_list.append(seat)
    return jsonify(seat_list), 200

@seat_bp.route("/seats/page", methods=["GET"])
def seats_page():
    return render_template("seat.html")

@seat_bp.route("/book_tickets", methods=["POST"])
def book_tickets():
    try:
        data = request.get_json()
        # Xử lý dữ liệu đặt vé ở đây
        return jsonify({"message": "Đặt vé thành công!"}), 200
    except Exception as e:
        return jsonify({"message": f"Lỗi: {e}"}), 500
