from pymongo import MongoClient
from datetime import datetime
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"


class PaymentMethod(Enum):
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    PAYPAL = "PayPal"
    CASH = "Cash"


class Payment:
    def __init__(self, payment_id, user_id, event_show_id=None, amount=0,
                 payment_method=PaymentMethod.CASH, seat_id=None, currency="USD", transaction_fee=0):
        self.payment_id = payment_id
        self.user_id = user_id  # Liên kết với User qua user_id
        self.event_show_id = event_show_id  # Liên kết với Event_Show qua event_show_id
        self.amount = amount
        self.payment_method = payment_method
        self.seat_id = seat_id  # ID ghế ngồi cho show cụ thể
        self.status = PaymentStatus.PENDING
        self.currency = currency
        self.transaction_fee = transaction_fee

    def process_payment(self):
        if self.amount > 0:
            self.status = PaymentStatus.COMPLETED
            return True
        raise Exception("Invalid payment amount.")

    def to_json(self):
        # Tạo mô tả cho `Event_Show`
        if self.event_show_id:
            show_type = "Event_Show"
            show_id = self.event_show_id
        else:
            raise Exception("No show selected for payment.")

        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "show_id": show_id,
            "show_type": show_type,
            "amount": self.amount,
            "payment_method": self.payment_method.value,
            "seat_id": self.seat_id,
            "status": self.status.value,
            "timestamp": datetime.now().isoformat(),
            "currency": self.currency,
            "description": f"{show_type} ticket purchase",
            "transaction_fee": self.transaction_fee
        }

    def save_to_mongodb(self):
        client = MongoClient("mongodb://localhost:27017/?directConnection=true")
        db = client["concert_booking"]
        payments_collection = db["payments"]
        payments_collection.insert_one(self.to_json())


if __name__ == "__main__":
    user_id = "user_001"
    seat = "seat_001"

    # Gán `event_show_id` cố định cho `Event_Show`
    event_show_id = "event_001"

    # Tạo đối tượng Payment cho `Event_Show`
    payment = Payment(
        payment_id="pay_001",
        user_id=user_id,
        event_show_id=event_show_id,
        amount=100,
        payment_method=PaymentMethod.CREDIT_CARD,
        seat_id=seat,
        currency="USD",
        transaction_fee=2.50
    )

    try:
        if payment.process_payment():
            payment.save_to_mongodb()
            print("Payment saved successfully.")
            print("Payment JSON:", payment.to_json())
    except Exception as e:
        print("Error during payment processing:", str(e))
