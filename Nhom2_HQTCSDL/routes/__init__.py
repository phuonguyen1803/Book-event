import os

from flask import Blueprint
# routes/__init__.py
from flask import Blueprint
def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    mongo.init_app(app)  # Khởi tạo mongo với ứng dụng
    return app

admin_bp = Blueprint('admin', __name__)
user_bp = Blueprint('user', __name__)
event_bp = Blueprint('event', __name__)
ticket_bp = Blueprint('ticket', __name__)
seat_bp = Blueprint('seat', __name__)
payment_bp = Blueprint('payment', __name__)

from .admin import *
from .user import *
from .event import *
from .ticket import *
from .seat import *
from .payment import *
