from flask import Flask, Blueprint, render_template, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from enum import Enum
import os
import json
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)
seat_bp = Blueprint('seat', __name__)

# Thiết lập MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["concert_booking"]
seats_collection = db["seats"]

class SeatStatus(Enum):
    AVAILABLE = "Available"
    BOOKED = "Booked"
    UNAVAILABLE = "Unavailable"

class SeatType(Enum):
    VIP = "VIP"
    STANDARD = "Standard"
    BALCONY = "Balcony"

class Seat:
    def __init__(self, seat_number, seat_type, price, show_id):
        self.id = ObjectId()
        self.seat_number = seat_number
        self.seat_type = SeatType[seat_type]
        self.price = price
        self.status = SeatStatus.AVAILABLE
        self.show_id = show_id
        self.show_type = "Event_Show"

    def book(self):
        if self.status == SeatStatus.AVAILABLE:
            self.status = SeatStatus.BOOKED
            return True
        return False

    def release(self):
        self.status = SeatStatus.AVAILABLE

    def to_dict(self):
        return {
            "id": str(self.id),
            "seat_number": self.seat_number,
            "seat_type": self.seat_type.name,
            "price": self.price,
            "status": self.status.name,
            "show_id": self.show_id,
            "show_type": self.show_type
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def save_to_mongodb(self):
        """Lưu thông tin ghế vào MongoDB."""
        seats_collection.insert_one(self.to_dict())

    @classmethod
    def get_seat_by_id(cls, seat_id):
        """Lấy ghế từ MongoDB theo ID."""
        seat_data = seats_collection.find_one({"_id": ObjectId(seat_id)})
        if seat_data:
            seat = cls(
                seat_number=seat_data['seat_number'],
                seat_type=seat_data['seat_type'],
                price=seat_data['price'],
                show_id=seat_data['show_id']
            )
            seat.id = seat_data['_id']
            seat.status = SeatStatus[seat_data['status']]
            return seat
        return None
seat_bp = Blueprint('seat', __name__)

@seat_bp.route('/seat')
def seat():
    return render_template('seat.html')

@seat_bp.route('/seat/submit_selection', methods=['POST'])
def submit_selection():
    data = request.json  # Lấy dữ liệu từ yêu cầu POST
    client = MongoClient("mongodb://localhost:27017/?directConnection=true")
    db = client["concert_booking"]
    result = db.seats.insert_one(data)
    return jsonify({"message": "Đặt vé thành công!", "id": str(result.inserted_id)})

if __name__ == "__main__":
    # Ví dụ sử dụng
    show_id = "show_001"
    seat = Seat(seat_number="A1", seat_type="VIP", price=100.0, show_id=show_id)
    seat.save_to_mongodb()
    print(seat.to_json())

    retrieved_seat = Seat.get_seat_by_id(str(seat.id))
    if retrieved_seat:
        print(retrieved_seat.to_json())

    app.run(debug=True)
