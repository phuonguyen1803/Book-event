import os
from functools import wraps
from flask import Flask, jsonify, request, g, render_template, logging
from flask_bcrypt import Bcrypt
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime
import jwt
from flask_caching import Cache
from app import mongo
from flask_limiter import Limiter
import logging

# Load các biến môi trường từ file .env
load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)

# Khóa bí mật cho JWT
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'mysecret')

# Kết nối đến MongoDB
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['concert_booking']
print("Kết nối MongoDB thành công!")

# Hàm xác thực JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data["_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 403
        return f(*args, **kwargs)
    return decorated

# Middleware xác thực admin
def admin_auth_middleware(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        try:
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            admin_id = decoded_token.get('_id')
            admin = db.admins.find_one({"_id": ObjectId(admin_id)})
            if not admin:
                return jsonify({"message": "Unauthorized"}), 401
            request.admin_id = admin_id
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        return func(*args, **kwargs)

    return decorated_function

@app.route("/")
def home():
    return "Chào mừng bạn đến với hệ thống đặt vé concert!"

@app.route("/admin")
def admin_page():
    print("Truy cập vào trang admin...")
    return render_template("admin.html")

# Route đăng ký admin
@app.route("/admin/signup", methods=["POST"])
def admin_signup():
    new_admin = request.get_json()
    if not new_admin or not new_admin.get("admin_email") or not new_admin.get("admin_password"):
        return jsonify({"message": "Missing required fields: admin_email, admin_password"}), 400

    existing_admin = db.admins.find_one({"admin_email": new_admin["admin_email"]})
    if existing_admin:
        return jsonify({"message": "Admin email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(new_admin["admin_password"]).decode("utf-8")
    admin = {
        "admin_email": new_admin["admin_email"],
        "admin_password": hashed_password,
        "admin_name": new_admin["admin_name"],
        "is_admin": True
    }
    db.admins.insert_one(admin)
    return jsonify({"message": "Signup successful"}), 201

# Route đăng nhập admin
@app.route("/admin/login", methods=["POST"])
def admin_login():
    login_data = request.get_json()
    admin = db.admins.find_one({"admin_email": login_data["admin_email"], "is_admin": True})
    if admin and bcrypt.check_password_hash(admin["admin_password"], login_data["admin_password"]):
        token = jwt.encode({"_id": str(admin["_id"])}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"message": "Login successful", "token": token}), 200
    return jsonify({"message": "Wrong credentials"}), 400

# Route đăng ký người dùng
@app.route("/user/signup", methods=["POST"])
def user_signup():
    new_user = request.get_json()
    if not new_user or not new_user.get("user_email") or not new_user.get("user_password"):
        return jsonify({"message": "Missing required fields: user_email, user_password"}), 400

    existing_user = db.users.find_one({"user_email": new_user["user_email"]})
    if existing_user:
        return jsonify({"message": "User email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(new_user["user_password"]).decode("utf-8")
    user = {
        "user_email": new_user["user_email"],
        "user_password": hashed_password,
        "user_name": new_user["user_name"],
        "wallet_balance": 1500,
        "bio": new_user.get("bio"),
        "membership_type": new_user.get("membership_type"),
        "gender": new_user.get("gender"),
        "user_status": 'active',
        "dob": new_user.get("dob"),
        "event_show_bookings": []
    }
    db.users.insert_one(user)
    return jsonify({"message": "Signup successful"}), 201

# Quản lý chỗ ngồi
@app.route("/seat/create", methods=["POST"])
def create_seat():
    seat_data = request.get_json()
    seat = {
        "row": seat_data["row"],
        "column": seat_data["column"],
        "status": "available",
        "event_show_id": seat_data["event_show_id"]
    }
    db.seats.insert_one(seat)
    return jsonify({"message": "Seat created successfully"}), 201

@app.route("/seat/update/<string:seat_id>", methods=["PUT"])
def update_seat(seat_id):
    seat_data = request.get_json()
    db.seats.update_one({"_id": ObjectId(seat_id)}, {"$set": seat_data})
    return jsonify({"message": "Seat updated successfully"}), 200

@app.route("/seat/delete/<string:seat_id>", methods=["DELETE"])
def delete_seat(seat_id):
    db.seats.delete_one({"_id": ObjectId(seat_id)})
    return jsonify({"message": "Seat deleted successfully"}), 200

# Quản lý vé
@app.route("/ticket/create", methods=["POST"])
def create_ticket():
    ticket_data = request.get_json()
    ticket = {
        "user_id": ticket_data["user_id"],
        "event_show_id": ticket_data["event_show_id"],
        "seat_id": ticket_data["seat_id"],
        "price": ticket_data["price"],
        "status": "booked",
        "booking_date": datetime.now()
    }
    db.tickets.insert_one(ticket)
    db.seats.update_one({"_id": ObjectId(ticket_data["seat_id"])}, {"$set": {"status": "booked"}})
    return jsonify({"message": "Ticket created successfully"}), 201

@app.route("/ticket/<string:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    ticket = db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if ticket:
        ticket["_id"] = str(ticket["_id"])
        return jsonify(ticket), 200
    return jsonify({"message": "Ticket not found"}), 404

# Quản lý thanh toán
@app.route("/payment/process", methods=["POST"])
def process_payment():
    payment_data = request.get_json()
    user = db.users.find_one({"_id": ObjectId(payment_data["user_id"])})
    ticket = db.tickets.find_one({"_id": ObjectId(payment_data["ticket_id"])})

    if not user or not ticket:
        return jsonify({"message": "User or ticket not found"}), 404

    if user["wallet_balance"] < ticket["price"]:
        return jsonify({"message": "Insufficient balance"}), 400

    new_balance = user["wallet_balance"] - ticket["price"]
    db.users.update_one({"_id": ObjectId(payment_data["user_id"])}, {"$set": {"wallet_balance": new_balance}})
    db.tickets.update_one({"_id": ObjectId(payment_data["ticket_id"])}, {"$set": {"status": "paid"}})

    payment = {
        "user_id": payment_data["user_id"],
        "ticket_id": payment_data["ticket_id"],
        "amount": ticket["price"],
        "status": "completed",
        "payment_date": datetime.now()
    }
    db.payments.insert_one(payment)
    return jsonify({"message": "Payment processed successfully"}), 201
# Hàm giúp chuyển đổi ObjectId thành chuỗi
def serialize_objectid(data):
    if isinstance(data, list):
        return [serialize_objectid(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_objectid(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    return data

# Middleware để xác thực JWT
@app.before_request
def authenticate():
    token = request.headers.get("Authorization")
    if token:
        try:
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = decoded["_id"]
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401
    elif request.endpoint not in ["user_login", "user_signup"]:
        return jsonify({"message": "Token is missing!"}), 403

# ----------------- USER ROUTES -----------------
@app.route('/api/users', methods=['GET'])
@admin_auth_middleware
def get_users():
    users = list(mongo.db.users.find({}, {"user_password": 0}))  # Không trả về mật khẩu
    return jsonify(serialize_objectid(users)), 200

@app.route('/api/users', methods=['POST'])
@admin_auth_middleware
def add_user():
    data = request.get_json()
    if not data or not data.get('user_email') or not data.get('user_password'):
        return jsonify({"message": "Missing required fields: user_email, user_password"}), 400

    data['user_password'] = bcrypt.generate_password_hash(data['user_password']).decode('utf-8')
    mongo.db.users.insert_one(data)
    return jsonify({"message": "User added successfully"}), 201

@app.route('/api/users/<user_id>', methods=['PUT'])
@admin_auth_middleware
def update_user(user_id):
    data = request.get_json()
    if 'user_password' in data:
        data['user_password'] = bcrypt.generate_password_hash(data['user_password']).decode('utf-8')
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": data})
    return jsonify({"message": "User updated successfully"}), 200

@app.route('/api/users/<user_id>', methods=['DELETE'])
@admin_auth_middleware
def delete_user(user_id):
    result = mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"message": "User deleted successfully"}), 204

@app.route("/user/signup", methods=["POST"])
def register_user():  # Đổi tên hàm
    new_user = request.get_json()
    hashed_password = bcrypt.generate_password_hash(new_user["user_password"]).decode('utf-8')
    user = {
        "user_email": new_user["user_email"],
        "user_password": hashed_password,
        "user_name": new_user["user_name"],
        "wallet_balance": 1500,
        "bio": new_user["bio"],
        "membership_type": new_user["membership_type"],
        "gender": new_user["gender"],
        "user_status": 'active',
        "dob": new_user["dob"],
        "movie_show_bookings": [],
        "event_show_bookings": []
    }
    mongo.db.users.insert_one(user)
    return jsonify({"message": "Signup successful"}), 201

@app.route("/user/login", methods=["POST"])
def user_login():
    login_data = request.get_json()
    user = mongo.db.users.find_one({"user_email": login_data["user_email"]})
    if not user:
        return jsonify({"message": "Wrong Email"}), 400
    if bcrypt.check_password_hash(user["user_password"], login_data["user_password"]):
        token = jwt.encode({"_id": str(user["_id"])}, app.config['SECRET_KEY'], algorithm="HS256")
        logging.info(f"User {login_data['user_email']} logged in")
        return jsonify({"message": "Login successful", "token": token, "username": user["user_name"]}), 200
    return jsonify({"message": "Wrong password!"}), 400

# ----------------- EVENT ROUTES -----------------
@app.route("/event/add", methods=["POST"])
def add_event():
    new_event = request.get_json()
    mongo.db.events.insert_one(new_event)
    return jsonify({"message": "Event added successfully"}), 201

@app.route("/events/get", methods=["GET"])
def get_all_events():
    all_events = list(mongo.db.events.find())
    return jsonify(serialize_objectid(all_events)), 200

@app.route("/event_shows/<string:event_id>", methods=["GET"])
def get_related_event_shows(event_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        return jsonify({"message": "Event not found"}), 404

    event_shows = list(mongo.db.event_shows.find({"event_id": event_id}))
    updated_event_shows = []
    for event_show in event_shows:
        event_show["_id"] = str(event_show["_id"])
        event_show["event_name"] = event["event_name"]
        updated_event_shows.append(event_show)
    return jsonify(updated_event_shows), 200

# ----------------- TICKET ROUTES -----------------
@app.route('/api/tickets', methods=['GET'])
@admin_auth_middleware
def get_tickets():
    tickets = list(mongo.db.tickets.find())
    return jsonify(serialize_objectid(tickets)), 200

@app.route('/api/tickets', methods=['POST'])
@admin_auth_middleware
def add_ticket():
    data = request.get_json()
    mongo.db.tickets.insert_one(data)
    return jsonify({"message": "Ticket added successfully"}), 201

@app.route('/api/tickets/<ticket_id>', methods=['PUT'])
@admin_auth_middleware
def update_ticket(ticket_id):
    data = request.get_json()
    mongo.db.tickets.update_one({"_id": ObjectId(ticket_id)}, {"$set": data})
    return jsonify({"message": "Ticket updated successfully"}), 200

@app.route('/api/tickets/<ticket_id>', methods=['DELETE'])
@admin_auth_middleware
def delete_ticket(ticket_id):
    result = mongo.db.tickets.delete_one({"_id": ObjectId(ticket_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "Ticket not found"}), 404
    return jsonify({"message": "Ticket deleted successfully"}), 204

# ----------------- SEAT ROUTES -----------------
@app.route('/api/seats', methods=['GET'])
@admin_auth_middleware
def get_seats():
    seats = list(mongo.db.seats.find())
    return jsonify(serialize_objectid(seats)), 200

@app.route('/api/seats', methods=['POST'])
@admin_auth_middleware
def add_seat():
    data = request.get_json()
    mongo.db.seats.insert_one(data)
    return jsonify({"message": "Seat added successfully"}), 201

# ----------------- PAYMENT ROUTE -----------------
@app.route('/api/payments', methods=['POST'])
def process_payment_v1():
    # Xử lý thanh toán
    pass

@app.route('/api/payments/other', methods=['POST'])
def process_payment_v2():
    # Xử lý thanh toán khác
    pass

# ----------------- LIMITER -----------------
# Khởi tạo Limiter mà không truyền đối số
limiter = Limiter(key_func=get_remote_address)  # Đặt key_func khi khởi tạo

# Đăng ký Limiter với ứng dụng
limiter.init_app(app)

@app.route('/api/some_endpoint', methods=['GET'])
@limiter.limit("5 per minute")  # Giới hạn 5 yêu cầu mỗi phút cho endpoint này
def some_function():
    return jsonify({"message": "This is a limited endpoint."}), 200
# ----------------- SWAGGER -----------------
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'  # Tài liệu Swagger JSON
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "My API"}
)

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
# Cấu hình Redis cho caching
cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})

@app.route('/events', methods=['GET'])
@cache.cached(timeout=300)  # Cache kết quả trong 5 phút
def get_events():
    # Giả lập lấy danh sách sự kiện từ cơ sở dữ liệu
    events = [
        {"id": 1, "name": "Concert A"},
        {"id": 2, "name": "Concert B"}
    ]
    return jsonify(events)
@app.route('/users/<int:user_id>/bookings', methods=['GET'])
def get_user_bookings(user_id):
    # Giả lập lịch sử đặt vé
    bookings = [
        {"booking_id": 1, "event": "Concert A", "date": "2024-11-01"},
        {"booking_id": 2, "event": "Concert B", "date": "2024-11-05"}
    ]
    return jsonify(bookings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)