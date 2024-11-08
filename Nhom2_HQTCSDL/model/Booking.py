from pymongo import MongoClient
from datetime import datetime
from enum import Enum
from bson import ObjectId

# Định nghĩa các trạng thái đặt chỗ
class BookingStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"

# Định nghĩa các trạng thái thanh toán
class PaymentStatus(Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"

# Định nghĩa các phương thức thanh toán
class PaymentMethod(Enum):
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    PAYPAL = "PayPal"
    CASH = "Cash"

# Lớp Event (sự kiện hòa nhạc)
class Event:
    def __init__(self, artist, venue, date, time, event_id=None):
        self.event_id = ObjectId() if event_id is None else ObjectId(event_id)
        self.artist = artist
        self.venue = venue
        self.date = date
        self.time = time

    def to_dict(self):
        return {
            "event_id": str(self.event_id),
            "artist": self.artist,
            "venue": self.venue,
            "date": self.date,
            "time": self.time
        }

# Lớp Booking (đặt chỗ)
class Booking:
    def __init__(self, user_id, seat, price, event=None, booking_status=BookingStatus.PENDING,
                 payment_status=PaymentStatus.PENDING, payment_method=None, booking_id=None):
        self.booking_id = ObjectId() if booking_id is None else ObjectId(booking_id)  # ID đặt chỗ
        self.user_id = user_id  # Không chuyển đổi user_id thành ObjectId
        self.seat = seat  # Ghế được đặt
        self.price = price  # Giá vé
        self.event = event  # Tham chiếu đến sự kiện (nếu có)
        self.booking_status = booking_status
        self.payment_status = payment_status
        self.payment_method = payment_method
        self.timestamp = datetime.now()  # Thời gian đặt chỗ

    def to_dict(self):
        booking_data = {
            "booking_id": str(self.booking_id),
            "user_id": str(self.user_id),
            "seat": self.seat,
            "price": self.price,
            "booking_status": self.booking_status.name,
            "payment_status": self.payment_status.name,
            "payment_method": self.payment_method.name if self.payment_method else None,
            "timestamp": self.timestamp.isoformat()
        }
        if self.event:
            booking_data["event"] = self.event.to_dict()  # Thông tin về sự kiện
        return booking_data

# Hệ thống đặt vé
class TicketBookingSystem:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["concert_booking"]
        self.bookings_collection = self.db["bookings"]
        self.events_collection = self.db["events"]

    # Tạo và lưu Event vào MongoDB
    def create_event(self, artist, venue, date, time):
        event = Event(artist=artist, venue=venue, date=date, time=time)
        self.events_collection.insert_one(event.to_dict())
        return event

    # Tạo đặt chỗ cho Event
    def create_booking(self, user_id, seat, price, event=None, payment_method=None):
        booking = Booking(
            user_id=user_id,
            seat=seat,
            price=price,
            event=event,
            payment_method=payment_method
        )
        self.bookings_collection.insert_one(booking.to_dict())
        return booking

if __name__ == "__main__":
    booking_system = TicketBookingSystem()

    # Tạo sự kiện hòa nhạc mới (Event)
    event = booking_system.create_event(
        artist="Artist Name",
        venue="Venue Name",
        date="2024-12-31",
        time="20:00"
    )
    print(f"Event created: {event.to_dict()}")

    # Tạo đặt chỗ cho Event
    booking_event = booking_system.create_booking(
        user_id="user_002",
        seat="B1",
        price=150.00,
        event=event,
        payment_method=PaymentMethod.PAYPAL
    )
    print("Booking for Event created:", booking_event.to_dict())
