from functools import wraps
from authlib.jose import jwt
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_bcrypt import Bcrypt
from app import mongo  # Import mongo từ app

bcrypt = Bcrypt()
user_bp = Blueprint('user', __name__)

def create_token(user_id, role):
    """Hàm để tạo JWT token."""
    token_data = {
        "_id": str(user_id),
        "role": role
    }
    return jwt.encode({"alg": "HS256"}, token_data, current_app.config['SECRET_KEY'])

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('user_email')
        password = request.form.get('user_password')

        user = mongo.db.users.find_one({"user_email": email})
        if not user or not bcrypt.check_password_hash(user["user_password"], password):
            return render_template('login.html', error="Invalid credentials")

        return redirect(url_for('home'))  # Redirect đến trang chính sau khi đăng nhập thành công

    return render_template('login.html')  # Render trang đăng nhập
@user_bp.route('/user/signup', methods=['POST'])
def user_signup():
    signup_data = request.get_json()  # Lấy dữ liệu JSON từ yêu cầu

    existing_user = mongo.db.users.find_one({"user_email": signup_data["user_email"]})
    if existing_user:
        return jsonify({"message": "Email already exists"}), 400

    # Hash mật khẩu người dùng
    hashed_password = bcrypt.generate_password_hash(signup_data["user_password"]).decode("utf-8")
    user = {
        "user_email": signup_data["user_email"],
        "user_password": hashed_password,
        "user_name": signup_data["user_name"],
        "wallet_balance": 1500,
        "bio": signup_data.get("bio"),
        "membership_type": signup_data.get("membership_type"),
        "gender": signup_data.get("gender"),
        "user_status": 'active',
        "dob": signup_data.get("dob"),
        "event_show_bookings": [],
        "role": signup_data.get("role", "user")
    }

    try:
        mongo.db.users.insert_one(user)  # Lưu người dùng vào MongoDB
        return jsonify({"message": "Signup successful"}), 200
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")  # In lỗi ra console
        return jsonify({"message": "Error saving data"}), 500

@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        new_user = {
            "user_email": request.form.get('user_email'),
            "user_password": request.form.get('user_password'),
            "user_name": request.form.get('user_name'),
            "bio": request.form.get('bio'),
            "membership_type": request.form.get('membership_type'),
            "gender": request.form.get('gender'),
            "dob": request.form.get('dob')
        }

        existing_user = mongo.db.users.find_one({"user_email": new_user["user_email"]})
        if existing_user:
            return render_template('signup.html', error="Email already exists")

        # Hash mật khẩu người dùng
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
            "event_show_bookings": [],
            "role": new_user.get("role", "user")
        }
        mongo.db.users.insert_one(user)
        return redirect(url_for('user.login'))  # Redirect về trang đăng nhập sau khi đăng ký thành công

    return render_template('signup.html')  # Render trang đăng ký

@user_bp.route('/user/login', methods=['POST'])
def user_login():
    login_data = request.get_json()
    user = mongo.db.users.find_one({"user_email": login_data["user_email"]})
    if not user:
        return jsonify({"message": "Wrong Email"}), 400

    # Kiểm tra mật khẩu
    if bcrypt.check_password_hash(user["user_password"], login_data["user_password"]):
        # Tạo token với role
        token = create_token(user["_id"], user["role"])
        return jsonify({"message": "Login successful", "token": token, "username": user["user_name"]}), 200

    return jsonify({"message": "Wrong password!"}), 400

def admin_auth_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            # Tách token và giải mã
            data = jwt.decode(token.split(" ")[1], current_app.config['SECRET_KEY'])
            if data.get("role") != "admin":
                return jsonify({"message": "Unauthorized: Admin access required!"}), 403
        except Exception as e:
            return jsonify({"message": "Token is invalid!"}), 403

        return f(*args, **kwargs)

    return decorated_function

@user_bp.route("/admin/only", methods=["GET"])
@admin_auth_middleware
def admin_only_view():
    return jsonify({"message": "Welcome, admin!"}), 200

