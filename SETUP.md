# 🚀 Setup Guide - Clothing Rental System

## Quick Start (Development)

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already created with default settings. You can modify it if needed.

**Important**: Email is disabled by default (MAIL_USERNAME is empty). Emails will be printed to console.

### 3. Initialize Database

```bash
# Initialize database with sample data
python init_db.py
```

This will create:
- **Admin account**: `admin@example.com` / `admin123`
- **Customer account**: `customer1@example.com` / `customer123`
- 5 categories
- 9 products
- 25+ inventory items
- 3 discount codes

### 4. Run the Application

```bash
python run.py
```

The app will be available at: **http://localhost:5000**

---

## 🧪 Testing the System

### Login as Admin

1. Go to http://localhost:5000/auth/login
2. Email: `admin@example.com`
3. Password: `admin123`
4. You'll be redirected to Admin Dashboard

**What you can do**:
- View all bookings
- Approve/reject bookings
- Assign inventory codes
- Manage inventory status
- View reports
- Create discount codes

### Login as Customer

1. Go to http://localhost:5000/auth/login
2. Email: `customer1@example.com`
3. Password: `customer123`

**What you can do**:
- Browse products
- Add to cart
- Create booking (checkout)
- View my bookings
- Write reviews (after completing booking)

### Create a Test Booking

1. Login as customer
2. Browse products → Add items to cart
3. Go to Cart → Checkout
4. Fill in rental dates:
   - **Rental Start**: Tomorrow 10:00 AM
   - **Rental End**: 3 days later 10:00 AM
5. Enter CCCD: `001099001234`
6. Optional: Use discount code `SALE50`
7. Submit booking

**Result**: Booking created with status PENDING

### Approve the Booking (as Admin)

1. Login as admin
2. Go to Bookings → Pending tab
3. Click on the booking
4. Assign inventory codes (e.g., VEST-D-001, SHOE-001)
5. Click "Approve"

**Result**: Booking status → APPROVED, email sent (printed to console)

### Test Price Calculation

**Clothing Example** (Vest - 200,000đ base):
- 1 day: 200,000đ
- 2 days: 410,000đ (200k + 210k)
- 3 days: 630,000đ (200k + 210k + 220k)
- 4 days: 850,000đ (+ 220k)
- 5 days: 1,080,000đ (+ 230k)

**Accessory Example** (Tie - 30,000đ):
- 1 day: 30,000đ
- 5 days: 150,000đ (30k × 5)

---

## 🔄 Testing Workflows

### Complete Workflow: Clothing Item

```
PENDING → APPROVED → RENTING → RETURNED_CLEANING → COMPLETED

1. Customer books vest
2. Admin approves & assigns VEST-D-001
3. Customer picks up → Admin clicks "Mark as Renting"
4. Customer returns → Admin clicks "Received (OK)"
   → Status: RETURNED_CLEANING
   → Inventory: maintenance
5. After cleaning → Admin clicks "Cleaning Completed"
   → Status: COMPLETED
   → Inventory: available
```

### Complete Workflow: Accessory Item

```
PENDING → APPROVED → RENTING → COMPLETED

1. Customer books tie
2. Admin approves & assigns TIE-001
3. Customer picks up → Mark as Renting
4. Customer returns → Admin clicks "Received (OK)"
   → Status: COMPLETED (direct)
   → Inventory: available (no cleaning needed)
```

### Workflow with Issues

```
RENTING → ISSUE → COMPLETED

1. Customer returns damaged item
2. Admin clicks "Add Penalty"
3. Select: Damage / Late / Lost
4. Enter amount & reason
5. Status → ISSUE
6. After resolving → Admin manually changes to COMPLETED
```

---

## 🤖 Testing Cronjobs

### Check Late Bookings

```bash
python cronjobs/check_late_bookings.py
```

**What it does**: Find RENTING bookings past rental_end → mark as LATE

### Send Reminders

```bash
python cronjobs/send_reminders.py
```

**What it does**: Send email reminders for pickups/returns tomorrow

### Auto-Complete Cleaning

```bash
python cronjobs/auto_complete_cleaning.py
```

**What it does**: Auto-complete bookings stuck in RETURNED_CLEANING > 3 days

---

## 📊 Sample Data Overview

### Products

| Product | Type | Base Price | Available |
|---------|------|------------|-----------|
| Vest đen cao cấp | clothing | 200,000đ | 4 bộ |
| Vest xám hiện đại | clothing | 180,000đ | 2 bộ |
| Áo dài đỏ | clothing | 150,000đ | 4 bộ |
| Váy cưới Princessa | clothing | 500,000đ | 0 bộ |
| Giày tây đen | accessory | 50,000đ | 5 đôi |
| Cà vạt lụa | accessory | 30,000đ | 5 chiếc |

### Discount Codes

| Code | Type | Value | Min Order | Usage Limit |
|------|------|-------|-----------|-------------|
| SALE50 | fixed | 50,000đ | 0đ | 100 |
| NEWYEAR2025 | percentage | 15% (max 100k) | 500,000đ | 50 |
| VIP10 | percentage | 10% | 300,000đ | Unlimited |

---

## 🐛 Troubleshooting

### Database locked error
```bash
# Stop the app
# Delete the database
rm clothing_rental.db

# Reinitialize
python init_db.py
```

### Import errors
```bash
# Make sure you're in virtual environment
which python
# Should show: /path/to/venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### Email not sending
Emails are disabled by default (printed to console only).

To enable real emails:
1. Edit `.env`
2. Set `MAIL_USERNAME` and `MAIL_PASSWORD`
3. Use App Password if using Gmail

---

## 📁 Project Structure

```
clothing-rental/
├── app/
│   ├── models/          # Database models
│   ├── services/        # Business logic (PriceCalculator, etc.)
│   ├── routes/          # API routes
│   ├── templates/       # Email templates
│   └── utils/           # Utilities
├── cronjobs/            # Automated tasks
├── .env                 # Environment config
├── init_db.py          # Database initialization
├── run.py              # App entry point
└── requirements.txt    # Dependencies
```

---

## 🎯 Next Steps

1. ✅ Test all workflows (create booking → approve → rent → return)
2. ✅ Test price calculation (clothing vs accessory)
3. ✅ Test discount codes
4. ✅ Test inventory management
5. ✅ Test cronjobs
6. 🔲 Add frontend templates (HTML/CSS) - optional
7. 🔲 Deploy to production server
8. 🔲 Setup real email (Gmail/SendGrid)
9. 🔲 Add payment gateway (if needed)
10. 🔲 Add more features

---

## 📞 Support

If you encounter any issues:
1. Check the console for error messages
2. Check the database: `sqlite3 clothing_rental.db`
3. Review the logic documentation in README.md

---

**Happy Testing! 🎉**
