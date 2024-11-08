from pymongo import MongoClient
from bson import ObjectId

# Kết nối tới MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['concert_booking']
events_collection = db['events']
event_show_collection = db['event_shows']  # Collection chứa các Event_Show


class EventShow:
    def __init__(self, event_id, date, language, start_time, end_time, price, total_seats, booked_seats=0, seat_map=None):
        self.event_id = event_id  # ID của sự kiện
        self.date = date
        self.language = language
        self.start_time = start_time
        self.end_time = end_time
        self.price = price
        self.total_seats = total_seats
        self.booked_seats = booked_seats
        self.seat_map = seat_map if seat_map is not None else [[0 for _ in range(10)] for _ in range(10)]  # Ma trận ghế

    def to_dict(self):
        return {
            "event_id": ObjectId(self.event_id),
            "date": self.date,
            "language": self.language,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "price": self.price,
            "total_seats": self.total_seats,
            "booked_seats": self.booked_seats,
            "seat_map": self.seat_map,
        }

    def save_to_db(self):
        """Lưu Event_Show vào MongoDB"""
        event_show_data = self.to_dict()
        result = event_show_collection.insert_one(event_show_data)
        return result.inserted_id

    @staticmethod
    def get_by_id(show_id):
        """Truy vấn Event_Show theo ID"""
        show_data = event_show_collection.find_one({"_id": ObjectId(show_id)})
        if show_data:
            return EventShow(
                event_id=show_data["event_id"],
                date=show_data["date"],
                language=show_data["language"],
                start_time=show_data["start_time"],
                end_time=show_data["end_time"],
                price=show_data["price"],
                total_seats=show_data["total_seats"],
                booked_seats=show_data["booked_seats"],
                seat_map=show_data["seat_map"]
            )
        return None


class Event:
    def __init__(self, event_name, languages, image_url=None, shows=None):
        """
        :param event_name: Tên sự kiện
        :param languages: Danh sách các ngôn ngữ
        :param image_url: URL của hình ảnh sự kiện
        :param shows: Danh sách các buổi biểu diễn liên kết
        """
        self.event_name = event_name
        self.languages = languages if languages is not None else []  # Danh sách các ngôn ngữ
        self.image_url = image_url
        self.shows = shows if shows is not None else []  # Danh sách các Event_Show

    def to_dict(self):
        return {
            "event_name": self.event_name,
            "languages": self.languages,  # Là danh sách thay vì một trường duy nhất
            "image_url": self.image_url,
            "shows": [ObjectId(show) for show in self.shows],  # Tham chiếu tới các ID của Event_Show
        }

    def save_to_db(self):
        """Lưu event vào MongoDB"""
        event_data = self.to_dict()
        result = events_collection.insert_one(event_data)
        return result.inserted_id  # Trả về ID của event mới được lưu

    @staticmethod
    def get_by_id(event_id):
        """Truy xuất event từ MongoDB theo ID"""
        event_data = events_collection.find_one({"_id": ObjectId(event_id)})
        if event_data:
            return Event(
                event_name=event_data["event_name"],
                languages=event_data["languages"],
                image_url=event_data.get("image_url"),
                shows=event_data.get("shows")
            )
        return None

    def add_show(self, show):
        """Thêm một Event_Show vào danh sách shows"""
        show_id = show.save_to_db()
        self.shows.append(show_id)
        events_collection.update_one(
            {"_id": ObjectId(self.save_to_db())},  # Cập nhật dựa trên event_id
            {"$push": {"shows": show_id}}
        )

    @staticmethod
    def get_all_events():
        """Lấy tất cả sự kiện từ MongoDB"""
        events = events_collection.find()
        return [Event(event_name=event['event_name'],
                      languages=event['languages'],
                      image_url=event.get('image_url'),
                      shows=event.get('shows', [])) for event in events]


# Ví dụ sử dụng

# Tạo một sự kiện mới
new_event = Event(
    event_name="Music Festival 2024",
    languages=["English", "Spanish"],
    image_url="http://example.com/event_image.jpg"
)

# Lưu sự kiện vào MongoDB
event_id = new_event.save_to_db()
print(f"Sự kiện đã được lưu với ID: {event_id}")

# Tạo một buổi biểu diễn cho sự kiện
new_event_show = EventShow(
    event_id=event_id,
    date="2024-10-30",
    language="English",
    start_time="18:00",
    end_time="20:00",
    price=50.0,
    total_seats=200
)

# Thêm buổi biểu diễn vào sự kiện
new_event.add_show(new_event_show)
print(f"Buổi biểu diễn đã được thêm vào sự kiện {new_event.event_name}")

# Truy vấn sự kiện và các buổi biểu diễn
queried_event = Event.get_by_id(event_id)
print(f"Truy xuất sự kiện: {queried_event.event_name}")
for show_id in queried_event.shows:
    queried_show = EventShow.get_by_id(show_id)
    print(f"Buổi biểu diễn: {queried_show.language} vào ngày {queried_show.date}")
