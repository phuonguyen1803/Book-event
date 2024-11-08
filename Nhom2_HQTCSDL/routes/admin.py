# routes/admin.py
from flask import Blueprint, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask import Flask
from flask_pymongo import PyMongo
import jwt

# Khởi tạo Flask app
app = Flask(__name__)

# Cấu hình MongoDB URI
app.config["MONGO_URI"] = "mongodb://localhost:27017/concert_booking"  # Thay 'your_database_name' bằng tên database của bạn
app.config['SECRET_KEY'] = 'your_secret_key'  # Thay thế bằng khóa bí mật của bạn

# Khởi tạo PyMongo
mongo = PyMongo(app)

# Kiểm tra kết nối đến MongoDB
try:
    mongo.db.command('ping')  # Kiểm tra kết nối
    print("Kết nối đến MongoDB thành công!")
except Exception as e:
    print("Không thể kết nối đến MongoDB:", e)

bcrypt = Bcrypt()
admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin/signup", methods=["POST"])
def admin_signup():
    new_admin = request.get_json()
    if not new_admin or not new_admin.get("admin_email") or not new_admin.get("admin_password"):
        return jsonify({"message": "Missing required fields: admin_email, admin_password"}), 400

    existing_admin = mongo.db.admins.find_one({"admin_email": new_admin["admin_email"]})
    if existing_admin:
        return jsonify({"message": "Admin email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(new_admin["admin_password"]).decode("utf-8")
    admin = {
        "admin_email": new_admin["admin_email"],
        "admin_password": hashed_password,
        "admin_name": new_admin.get("admin_name"),  # Sử dụng get để tránh lỗi nếu không có
        "is_admin": True
    }
    mongo.db.admins.insert_one(admin)  # Sửa thành mongo.db để lưu vào MongoDB
    return jsonify({"message": "Signup successful"}), 201

@admin_bp.route("/admin/login", methods=["POST"])
def admin_login():
    login_data = request.get_json()
    admin = mongo.db.admins.find_one({"admin_email": login_data["admin_email"], "is_admin": True})
    if admin and bcrypt.check_password_hash(admin["admin_password"], login_data["admin_password"]):
        token = jwt.encode({"_id": str(admin["_id"])}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"message": "Login successful", "token": token}), 200
    return jsonify({"message": "Wrong credentials"}), 400

@admin_bp.route("/admin", methods=["GET"])
def admin_page():
    return render_template("admin.html")

@admin_bp.route("/admin/list", methods=["GET"])
def list_admins():
    admins = mongo.db.admins.find()  # Giả sử bạn có một collection tên là 'admins'
    admin_list = []

    for admin in admins:
        admin["_id"] = str(admin["_id"])  # Chuyển ObjectId thành string
        admin_list.append(admin)

    return jsonify(admin_list), 200

@admin_bp.route("/admin/users", methods=["GET"])
def list_users():
    users = mongo.db.users.find()  # Thay 'users' bằng tên collection của bạn
    user_list = []

    for user in users:
        user["_id"] = str(user["_id"])  # Chuyển ObjectId thành string
        user_list.append(user)

    return jsonify(user_list), 200

@admin_bp.route("/admin/tickets", methods=["GET"])
def list_tickets():
    tickets = mongo.db.tickets.find()  # Thay 'tickets' bằng tên collection của bạn
    ticket_list = []

    for ticket in tickets:
        ticket["_id"] = str(ticket["_id"])  # Chuyển ObjectId thành string
        ticket_list.append(ticket)

    return jsonify(ticket_list), 200

@admin_bp.route("/admin/seats", methods=["GET"])
def list_seats():
    seats = mongo.db.seats.find()  # Thay 'seats' bằng tên collection của bạn
    seat_list = []

    for seat in seats:
        seat["_id"] = str(seat["_id"])  # Chuyển ObjectId thành string
        seat_list.append(seat)

    return jsonify(seat_list), 200

@admin_bp.route("/admin/payments", methods=["GET"])
def list_payments():
    payments = mongo.db.payments.find()  # Thay 'payments' bằng tên collection của bạn
    payment_list = []

    for payment in payments:
        payment["_id"] = str(payment["_id"])  # Chuyển ObjectId thành string
        payment_list.append(payment)

    return jsonify(payment_list), 200
