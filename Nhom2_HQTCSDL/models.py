# models.py
import os

from flask_pymongo import PyMongo

mongo = PyMongo()  # Khởi tạo PyMongo nhưng chưa kết nối
# app.py
from flask import Flask
from models import mongo

def create_app():
    app = Flask(__name__)

    # Cấu hình URI kết nối MongoDB
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/your_database")

    # Khởi tạo MongoDB với ứng dụng Flask
    mongo.init_app(app)  # Khởi tạo mongo với app

    # Đăng ký các blueprint
    from routes.seat import seat_bp
    app.register_blueprint(seat_bp)

    return app
