import os
class Config:
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'mysecret')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/concert_booking')
