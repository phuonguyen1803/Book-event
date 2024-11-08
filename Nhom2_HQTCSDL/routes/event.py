from bson import ObjectId
from flask import request, jsonify
from . import event_bp
from model import db

@event_bp.route("/event/add", methods=["POST"])
def add_event():
    new_event = request.get_json()
    db.events.insert_one(new_event)
    return jsonify({"message": "Event added successfully!"}), 201

@event_bp.route("/event/get/<event_id>", methods=["GET"])
def get_event(event_id):
    event = db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        return jsonify({"message": "Event not found!"}), 404
    return jsonify(event), 200

@event_bp.route("/events", methods=["GET"], endpoint="get_all_events_unique")  # Đổi tên endpoint
def get_all_events():
    events = db.events.find()
    events_list = [{**event, "_id": str(event["_id"])} for event in events]  # Chuyển ObjectId thành chuỗi
    return jsonify(events_list), 200
