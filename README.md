# 👗 Clothing Rental System

Hệ thống cho thuê quần áo và phụ kiện với logic tính giá đặc biệt cho 2 loại sản phẩm: Clothing (tăng dần) và Accessory (cố định).

## ✨ Tính năng chính

- ✅ **Phân loại sản phẩm**: Clothing vs Accessory với logic giá khác nhau
- ✅ **Tính giá thông minh**: Clothing tăng dần theo pattern đặc biệt, Accessory giá cố định
- ✅ **Quản lý kho 2 tầng**: Product (thông tin chung) + Inventory Items (bộ đồ vật lý)
- ✅ **Workflow phân biệt**: Clothing cần giặt (RETURNED_CLEANING), Accessory không cần
- ✅ **Cọc CCCD**: Không thu tiền online, chỉ cần số CCCD
- ✅ **Admin full control**: Duyệt đơn, gán mã bộ đồ, sửa đơn, tính phạt
- ✅ **Hệ thống mã giảm giá**: Fixed & Percentage với điều kiện
- ✅ **Email tự động**: Xác nhận, duyệt, nhắc nhở, hoàn thành
- ✅ **Cronjobs**: Check quá hạn, nhắc nhở, auto-complete

## 🚀 Cài đặt

### Yêu cầu

- Python 3.8+
- MySQL/PostgreSQL (hoặc SQLite cho dev)
- Redis (optional - cho caching & celery)

### Các bước

1. **Clone repository**
```bash
git clone <repo-url>
cd clothing-rental
```

2. **Tạo virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

3. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

4. **Cấu hình environment**
```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin của bạn
```

5. **Khởi tạo database**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. **Tạo admin user (optional)**
```bash
flask shell
>>> from app import db
>>> from app.models.user import User
>>> admin = User(
...     email='admin@example.com',
...     full_name='Admin',
...     phone='0901234567',
...     role='admin'
... )
>>> admin.set_password('admin123')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

7. **Chạy ứng dụng**
```bash
python run.py
# hoặc
flask run
```

Truy cập: http://localhost:5000

## 📊 Database Schema

### Core Tables
- `users` - Tài khoản (customer/admin)
- `categories` - Danh mục sản phẩm
- `products` - Sản phẩm (thông tin chung)
- `inventory_items` - Bộ đồ vật lý (VEST-001, VEST-002...)
- `bookings` - Đơn thuê
- `booking_items` - Chi tiết sản phẩm trong đơn
- `penalties` - Tiền phạt (hư, mất, trễ)
- `discount_codes` - Mã giảm giá
- `discount_usage` - Lịch sử dùng mã
- `reviews` - Đánh giá sản phẩm
- `booking_history` - Audit log

## 💰 Logic tính giá

### Clothing (Quần áo)
```
Ngày 1: price_base + 0k
Ngày 2: price_base + 10k
Ngày 3: price_base + 20k
Ngày 4: price_base + 20k
Ngày 5: price_base + 30k
Ngày 6: price_base + 30k
...
Pattern: Cứ 2 ngày tăng 10k
```

### Accessory (Phụ kiện)
```
Total = price_base × số ngày
Giá cố định, không tăng dần
```

### Tính ngày
```
total_days = CEILING(total_hours / 24)
Minimum: 1 ngày
```

## 🔄 Workflow

### Customer
1. Browse products → Add to cart
2. Checkout (chọn thời gian, điền CCCD)
3. PENDING → Chờ admin duyệt
4. APPROVED → Nhận đồ
5. RENTING → Sử dụng
6. Trả đồ → COMPLETED

### Admin
1. Duyệt đơn → Gán mã bộ đồ
2. Giao đồ → RENTING
3. Nhận đồ trả:
   - Clothing → RETURNED_CLEANING → Giặt xong → COMPLETED
   - Accessory → COMPLETED (trực tiếp)
   - Có vấn đề → ISSUE → Xử lý → COMPLETED

## 📧 Email Templates

- Xác nhận đặt hàng (PENDING)
- Đơn được duyệt (APPROVED)
- Đơn bị từ chối (REJECTED)
- Nhắc trước 1 ngày nhận đồ
- Nhắc trước 1 ngày trả đồ
- Quá hạn trả (LATE)
- Hoàn thành (COMPLETED)

## 🛠️ Cron Jobs

Chạy bằng Celery Beat hoặc system cron:

```bash
# Check quá hạn - mỗi giờ
0 * * * * python cronjobs/check_late_bookings.py

# Nhắc nhở - mỗi ngày 18:00
0 18 * * * python cronjobs/send_reminders.py

# Auto-complete cleaning - mỗi ngày 00:00
0 0 * * * python cronjobs/auto_complete_cleaning.py
```

## 📝 Development

### Create migration
```bash
flask db migrate -m "Description"
flask db upgrade
```

### Flask shell
```bash
flask shell
>>> from app import db
>>> from app.models import *
>>> # Your code here
```

### Run tests (coming soon)
```bash
pytest
```

## 🔐 Security

- Password hashing: bcrypt
- CSRF protection: Flask-WTF
- SQL Injection: SQLAlchemy ORM (parameterized queries)
- XSS: Jinja2 auto-escape
- Session: Secure cookies with HTTPS in production

## 📦 Project Structure

```
clothing-rental/
├── app/
│   ├── __init__.py
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   ├── routes/          # API routes
│   ├── templates/       # Jinja2 templates
│   ├── static/          # CSS, JS, images
│   └── utils/           # Utilities
├── migrations/          # Database migrations
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── run.py              # Entry point
└── README.md
```

## 👥 Roles

- **Customer**: Browse, booking, view own orders
- **Admin**: Full control (approve, assign codes, manage inventory, reports)

## 📄 License

MIT License

## 🤝 Contributing

Pull requests are welcome!

---

Made with ❤️ for clothing rental business
