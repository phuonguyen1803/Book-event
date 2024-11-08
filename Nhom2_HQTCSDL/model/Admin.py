from pymongo import MongoClient
from bson.objectid import ObjectId

# Kết nối tới MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client["concert_booking"]  # Chọn cơ sở dữ liệu

# Định nghĩa class Role
class Role:
    def __init__(self, role_name, permissions):
        self.role_name = role_name
        self.permissions = permissions

    def to_dict(self):
        return {
            "role_name": self.role_name,
            "permissions": self.permissions,
        }

# Định nghĩa class Admin
class Admin:
    def __init__(self, admin_name, admin_email, admin_password, role, is_admin=True):
        self.admin_name = admin_name
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.role = role  # Gán quyền cho quản trị viên
        self.is_admin = is_admin

    def to_dict(self):
        return {
            "admin_name": self.admin_name,
            "admin_email": self.admin_email,
            "admin_password": self.admin_password,  # Lưu ý: Không nên lưu mật khẩu dưới dạng văn bản
            "role": self.role.to_dict(),  # Chuyển đổi quyền thành từ điển
            "is_admin": self.is_admin,
        }

# Tạo một số đối tượng Role với quyền hạn khác nhau
admin_role = Role(
    role_name="Admin",
    permissions=["create", "read", "update", "delete"]  # Quyền quản trị viên đầy đủ
)

editor_role = Role(
    role_name="Editor",
    permissions=["create", "read", "update"]  # Quyền chỉnh sửa nhưng không xóa
)

viewer_role = Role(
    role_name="Viewer",
    permissions=["read"]  # Chỉ quyền xem
)

# Tạo một đối tượng Admin
new_admin = Admin(
    admin_name="Phuong Uyen",
    admin_email="225481214@vaa.edu.vn",
    admin_password="hanhbac18",
    role=admin_role
)

# Lưu Admin vào MongoDB
admin_collection = db["admins"]  # Chọn collection cho Admin
result = admin_collection.insert_one(new_admin.to_dict())  # Thêm đối tượng vào collection
print(f"Admin đã được lưu với ID: {result.inserted_id}")

# Lấy dữ liệu của Admin từ MongoDB
retrieved_admin = admin_collection.find_one({"_id": result.inserted_id})  # Tìm Admin bằng ID
if retrieved_admin:
    print("Admin đã được tìm thấy:", retrieved_admin)
else:
    print("Không tìm thấy Admin với ID này.")

