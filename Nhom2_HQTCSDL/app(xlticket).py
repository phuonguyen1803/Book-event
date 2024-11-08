from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from redis import Redis
import time
import logging
from pydantic import BaseModel, ValidationError

app = Flask(__name__)
# Kết nối đến MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['concert_booking']

# Kết nối đến Redis để quản lý khóa
redis_client = Redis()

# Cấu hình thời gian giữ vé mặc định
DEFAULT_RESERVATION_TIME_LIMIT = 300  # Thời gian giữ vé mặc định (giây)

# Cài đặt ghi log
logging.basicConfig(level=logging.INFO)

# Mô hình kiểm tra dữ liệu đầu vào
class BookingData(BaseModel):
    event_name: str
    number_of_tickets: int
    reservation_time_limit: int = DEFAULT_RESERVATION_TIME_LIMIT

# Hàm thử lấy khóa với thời gian chờ tối đa
def acquire_lock(event_name, operation, max_wait_time=3.0):
    """Thử lấy khóa với thời gian chờ tối đa."""
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if redis_client.set(event_name + operation, 'LOCK', ex=5, nx=True):
            return True
        time.sleep(0.1)
    return False

def release_lock(event_name, operation):
    """Giải phóng khóa cho sự kiện cụ thể."""
    redis_client.delete(event_name + operation)

@app.route('/book_ticket', methods=['POST'])
def book_ticket():
    """Đặt vé cho sự kiện."""
    data = request.get_json()

    # Kiểm tra đầu vào bằng Pydantic
    try:
        booking_data = BookingData(**data)
    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        return jsonify({"error": "Invalid input data", "details": e.errors()}), 400

    event_name = booking_data.event_name
    tickets_to_book = booking_data.number_of_tickets
    reservation_time_limit = booking_data.reservation_time_limit

    # Tìm vé cho sự kiện
    ticket = db.tickets.find_one({"event_name": event_name})

    if not ticket:
        logging.warning(f"Event not found: {event_name}")
        return jsonify({"error": "Event not found"}), 404

    # Kiểm tra xem có đủ vé không
    if ticket['sold_tickets'] + tickets_to_book > ticket['total_tickets']:
        return jsonify({"error": "Not enough tickets available"}), 400

    # Cố gắng thực hiện đặt vé với khóa
    max_retries = 5
    for attempt in range(max_retries):
        if not acquire_lock(event_name, "WLOCK"):
            if attempt == max_retries - 1:
                logging.warning(f"Failed to acquire WLOCK after multiple attempts for {event_name}")
                return jsonify({"error": "Failed to acquire WLOCK after multiple attempts"}), 408
            time.sleep(0.1)
            continue

        try:
            # Phase 1: Chuẩn bị
            start_time = time.time()
            with client.start_session() as session:
                session.start_transaction()
                prepare_successful = True

                # Kiểm tra vé
                ticket = db.tickets.find_one({"event_name": event_name}, session=session)

                if ticket['sold_tickets'] + tickets_to_book > ticket['total_tickets']:
                    prepare_successful = False  # Không đủ vé
                else:
                    # Tạo bản ghi giao dịch
                    db.transactions.insert_one({
                        "event_name": event_name,
                        "number_of_tickets": tickets_to_book,
                        "status": "reserved",  # Đặt giữ
                        "reserved_at": start_time,
                        "started_at": time.time(),
                        "ended_at": None,  # Chưa kết thúc
                        "cancellation_reason": None  # Không có lý do hủy
                    }, session=session)

                if not prepare_successful:
                    session.abort_transaction()
                    return jsonify({"error": "Not enough tickets available"}), 400

                # Phase 2: Hợp thức hóa
                while time.time() - start_time < reservation_time_limit:
                    db.tickets.update_one(
                        {"event_name": event_name},
                        {"$inc": {"sold_tickets": tickets_to_book}},
                        session=session
                    )
                    session.commit_transaction()
                    remaining_tickets = ticket['total_tickets'] - (ticket['sold_tickets'] + tickets_to_book)
                    return jsonify({
                        "message": "Tickets booked successfully",
                        "sold_tickets": ticket['sold_tickets'] + tickets_to_book,
                        "remaining_tickets": remaining_tickets  # Số vé còn lại
                    }), 200

                # Nếu hết thời gian
                session.abort_transaction()
                logging.warning(f"Reservation timed out for {event_name}")
                return jsonify({"error": "Reservation timed out"}), 408

        except (errors.PyMongoError, Exception) as e:
            session.abort_transaction()
            logging.error(f"Transaction aborted due to error: {str(e)} | Event: {event_name} | User input: {data}")
            return jsonify({"error": "Transaction aborted due to error", "details": str(e)}), 500
        finally:
            release_lock(event_name, "UNLOCK")

    return jsonify({"error": "Failed to book tickets after multiple attempts"}), 500

@app.route('/events', methods=['GET'])
def get_events():
    """Lấy danh sách các sự kiện."""
    events = list(db.tickets.find())
    for event in events:
        event['_id'] = str(event['_id'])  # Chuyển đổi ObjectId thành chuỗi
    return jsonify(events), 200

@app.route('/update_event', methods=['PUT'])
def update_event():
    """Cập nhật thông tin sự kiện."""
    data = request.get_json()
    event_name = data.get('event_name')
    new_data = data.get('new_data')

    if not event_name or not new_data:
        return jsonify({"error": "Invalid input data"}), 400

    if 'total_tickets' in new_data and new_data['total_tickets'] < 0:
        return jsonify({"error": "Total tickets cannot be negative"}), 400

    # Cố gắng thực hiện cập nhật với khóa
    if not acquire_lock(event_name, "WLOCK"):
        return jsonify({"error": "Failed to acquire WLOCK for update"}), 403

    try:
        result = db.tickets.update_one(
            {"event_name": event_name},
            {"$set": new_data}
        )

        if result.modified_count == 0:
            logging.warning(f"No event found or no changes made for {event_name}.")
            return jsonify({"error": "No event found or no changes made"}), 404

        return jsonify({"message": "Event updated successfully"}), 200
    finally:
        release_lock(event_name, "UNLOCK")  # Mở khóa an toàn

@app.route('/transaction_status', methods=['GET'])
def transaction_status():
    """Kiểm tra trạng thái giao dịch."""
    transaction_id = request.args.get('transaction_id')

    if not transaction_id:
        return jsonify({"error": "Transaction ID is required"}), 400

    # Tìm kiếm thông tin giao dịch trong cơ sở dữ liệu (nếu có)
    transaction = db.transactions.find_one({"transaction_id": transaction_id})

    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"transaction_id": transaction_id, "status": transaction['status']}), 200

# Thêm một hàm để đăng ký danh sách chờ
@app.route('/waitlist', methods=['POST'])
def waitlist():
    """Đăng ký danh sách chờ cho sự kiện."""
    data = request.get_json()

    try:
        booking_data = BookingData(**data)
    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        return jsonify({"error": "Invalid input data", "details": e.errors()}), 400

    event_name = booking_data.event_name
    # Thêm vào danh sách chờ
    db.waitlist.insert_one({
        "event_name": event_name,
        "number_of_tickets": booking_data.number_of_tickets,
        "requested_at": time.time()
    })

    return jsonify({"message": "Added to waitlist successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True, ssl_context=('path/to/cert.pem', 'path/to/key.pem'))  # Đảm bảo cập nhật đường dẫn đến chứng chỉ SSL
