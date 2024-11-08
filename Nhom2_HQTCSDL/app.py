import os
import logging
from flask import Flask, request
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_caching import Cache
from flask_pymongo import PyMongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure the application
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'mysecret')
app.config["MONGO_URI"] = os.getenv("MONGO_URI", 'mongodb://localhost:27017/concert_booking')

# Initialize Flask extensions
bcrypt = Bcrypt(app)
mongo = PyMongo(app)
limiter = Limiter(key_func=lambda: request.remote_addr)
cache = Cache(config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

# Đăng ký các blueprint
def register_blueprints(app):
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.event import event_bp
    from routes.ticket import ticket_bp
    from routes.seat import seat_bp
    from routes.payment import payment_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(seat_bp)
    app.register_blueprint(payment_bp)

# Chạy ứng dụng
def create_app():
    register_blueprints(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
