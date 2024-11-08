from pymongo import MongoClient
from bson import ObjectId
import json

class UserStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"

class MembershipType:
    REGULAR = "regular"
    PREMIUM = "premium"
    VIP = "VIP"

class Gender:
    MALE = "male"
    FEMALE = "female"
    OTHERS = "others"

class User:
    def __init__(self, user_email, user_password, user_name, wallet_balance=0.0, bio=None,
                 membership_type=MembershipType.REGULAR, gender=Gender.OTHERS, user_status=UserStatus.ACTIVE, dob=None,
                 event_show_bookings=None):
        self.id = ObjectId()
        self.user_email = user_email
        self.user_password = user_password
        self.user_name = user_name
        self.wallet_balance = wallet_balance
        self.bio = bio
        self.membership_type = membership_type
        self.gender = gender
        self.user_status = user_status
        self.dob = dob
        self.event_show_bookings = event_show_bookings if event_show_bookings is not None else []

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_email": self.user_email,
            "user_password": self.user_password,
            "user_name": self.user_name,
            "wallet_balance": self.wallet_balance,
            "bio": self.bio,
            "membership_type": self.membership_type,
            "gender": self.gender,
            "user_status": self.user_status,
            "dob": self.dob,
            "event_show_bookings": [str(booking_id) for booking_id in self.event_show_bookings]
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def save_to_mongodb(self):
        """Lưu thông tin người dùng vào MongoDB."""
        client = MongoClient("mongodb://localhost:27017/")
        db = client["concert_booking"]
        users_collection = db["users"]

        # Chuyển đổi đối tượng thành từ điển và lưu vào MongoDB
        users_collection.insert_one(self.to_dict())

    @classmethod
    def get_user_by_id(cls, user_id):
        """Lấy thông tin người dùng từ MongoDB theo ID."""
        client = MongoClient("mongodb://localhost:27017/")
        db = client["concert_booking"]
        users_collection = db["users"]

        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            user = cls(
                user_email=user_data['user_email'],
                user_password=user_data['user_password'],
                user_name=user_data['user_name'],
                wallet_balance=user_data.get('wallet_balance', 0.0),
                bio=user_data.get('bio'),
                membership_type=user_data.get('membership_type', MembershipType.REGULAR),
                gender=user_data.get('gender', Gender.OTHERS),
                user_status=user_data.get('user_status', UserStatus.ACTIVE),
                dob=user_data.get('dob'),
                event_show_bookings=user_data.get('event_show_bookings', [])
            )
            user.id = user_data['_id']
            return user
        return None


# Ví dụ sử dụng
if __name__ == "__main__":
    # Tạo một người dùng mới
    user = User(
        user_email="example@gmail.com",
        user_password="password123",
        user_name="John Doe",
        wallet_balance=500.0,
        bio="A music lover",
        membership_type=MembershipType.VIP,
        gender=Gender.MALE,
        user_status=UserStatus.ACTIVE,
        dob="1990-01-01",
        event_show_bookings=["event_show_001", "event_show_002"]
    )

    # Lưu người dùng vào MongoDB
    user.save_to_mongodb()

    # Lấy thông tin người dùng dưới dạng JSON
    print(user.to_json())

    # Lấy người dùng từ MongoDB
    retrieved_user = User.get_user_by_id(str(user.id))
    if retrieved_user:
        print(retrieved_user.to_json())
