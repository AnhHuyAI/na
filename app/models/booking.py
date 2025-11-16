from datetime import datetime
from app import db
import string
import random


class Booking(db.Model):
    """Booking model - Rental orders"""

    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)

    # Unique booking code (e.g., BK20251120001)
    booking_code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Customer
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Rental period
    rental_start = db.Column(db.DateTime, nullable=False, index=True)
    rental_end = db.Column(db.DateTime, nullable=False, index=True)
    total_days = db.Column(db.Integer, nullable=False)

    # Pricing
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)  # Before discount
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)  # After discount
    penalty_amount = db.Column(db.Numeric(10, 2), default=0)  # Penalties (damage, late, lost)

    # Discount code used
    discount_code_id = db.Column(db.Integer, db.ForeignKey('discount_codes.id', ondelete='SET NULL'), nullable=True)

    # Status: PENDING, APPROVED, RENTING, RETURNED_CLEANING, COMPLETED, LATE, ISSUE, REJECTED, CANCELLED
    status = db.Column(db.String(20), nullable=False, default='PENDING', index=True)

    # Customer info (copied at booking time for audit)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_id_card = db.Column(db.String(12), nullable=False)
    customer_address = db.Column(db.Text, nullable=True)
    customer_notes = db.Column(db.Text, nullable=True)

    # Admin notes
    admin_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # Admin tracking
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='bookings')
    approver = db.relationship('User', foreign_keys=[approved_by])
    discount_code = db.relationship('DiscountCode', back_populates='bookings')
    items = db.relationship('BookingItem', back_populates='booking', lazy='dynamic', cascade='all, delete-orphan')
    penalties = db.relationship('Penalty', back_populates='booking', lazy='dynamic', cascade='all, delete-orphan')
    history = db.relationship('BookingHistory', back_populates='booking', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Booking {self.booking_code}>'

    @staticmethod
    def generate_booking_code():
        """Generate unique booking code: BK + YYYYMMDD + Random5digits"""
        today = datetime.utcnow()
        date_str = today.strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=5))
        code = f'BK{date_str}{random_str}'

        # Ensure uniqueness
        while Booking.query.filter_by(booking_code=code).first():
            random_str = ''.join(random.choices(string.digits, k=5))
            code = f'BK{date_str}{random_str}'

        return code

    def get_final_amount(self):
        """Get final amount including penalties"""
        return float(self.total_price) + float(self.penalty_amount)

    def is_pending(self):
        return self.status == 'PENDING'

    def is_approved(self):
        return self.status == 'APPROVED'

    def is_renting(self):
        return self.status == 'RENTING'

    def is_returned_cleaning(self):
        return self.status == 'RETURNED_CLEANING'

    def is_completed(self):
        return self.status == 'COMPLETED'

    def is_late(self):
        return self.status == 'LATE'

    def is_issue(self):
        return self.status == 'ISSUE'

    def is_rejected(self):
        return self.status == 'REJECTED'

    def is_cancelled(self):
        return self.status == 'CANCELLED'

    def can_edit(self):
        """Check if booking can be edited"""
        return self.status in ['PENDING', 'APPROVED']

    def can_cancel(self):
        """Check if booking can be cancelled"""
        return self.status in ['PENDING', 'APPROVED']

    def get_status_badge_class(self):
        """Get Bootstrap badge class for status"""
        status_map = {
            'PENDING': 'warning',
            'APPROVED': 'info',
            'RENTING': 'success',
            'RETURNED_CLEANING': 'secondary',
            'COMPLETED': 'primary',
            'LATE': 'warning',
            'ISSUE': 'danger',
            'REJECTED': 'danger',
            'CANCELLED': 'secondary'
        }
        return status_map.get(self.status, 'secondary')

    def get_status_display(self):
        """Get Vietnamese display text for status"""
        status_map = {
            'PENDING': 'Chờ duyệt',
            'APPROVED': 'Đã duyệt',
            'RENTING': 'Đang thuê',
            'RETURNED_CLEANING': 'Đang giặt',
            'COMPLETED': 'Hoàn thành',
            'LATE': 'Quá hạn',
            'ISSUE': 'Có vấn đề',
            'REJECTED': 'Đã từ chối',
            'CANCELLED': 'Đã hủy'
        }
        return status_map.get(self.status, self.status)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'booking_code': self.booking_code,
            'status': self.status,
            'status_display': self.get_status_display(),
            'rental_start': self.rental_start.isoformat(),
            'rental_end': self.rental_end.isoformat(),
            'total_days': self.total_days,
            'subtotal': float(self.subtotal),
            'discount_amount': float(self.discount_amount),
            'total_price': float(self.total_price),
            'penalty_amount': float(self.penalty_amount),
            'final_amount': self.get_final_amount(),
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'created_at': self.created_at.isoformat()
        }


class BookingItem(db.Model):
    """Booking item model - Products in a booking"""

    __tablename__ = 'booking_items'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id', ondelete='SET NULL'), nullable=True)

    # Product info (snapshot at booking time)
    product_name = db.Column(db.String(255), nullable=False)
    product_type = db.Column(db.String(20), nullable=False)
    price_base = db.Column(db.Numeric(10, 2), nullable=False)

    # Calculated price for this item
    item_total = db.Column(db.Numeric(10, 2), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    booking = db.relationship('Booking', back_populates='items')
    product = db.relationship('Product', back_populates='booking_items')
    inventory_item = db.relationship('InventoryItem', back_populates='booking_items')

    def __repr__(self):
        return f'<BookingItem {self.product_name}>'

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_type': self.product_type,
            'price_base': float(self.price_base),
            'item_total': float(self.item_total),
            'inventory_item_code': self.inventory_item.item_code if self.inventory_item else None
        }


class Penalty(db.Model):
    """Penalty model - Fines for damages, losses, late returns"""

    __tablename__ = 'penalties'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)

    # Penalty type: 'damage', 'lost', 'late'
    penalty_type = db.Column(db.String(20), nullable=False)

    # Amount
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Description
    reason = db.Column(db.Text, nullable=False)

    # Created by admin
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    booking = db.relationship('Booking', back_populates='penalties')
    creator = db.relationship('User')

    def __repr__(self):
        return f'<Penalty {self.penalty_type} - {self.amount}>'

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'penalty_type': self.penalty_type,
            'amount': float(self.amount),
            'reason': self.reason,
            'created_at': self.created_at.isoformat()
        }


class BookingHistory(db.Model):
    """Booking history model - Audit trail for status changes"""

    __tablename__ = 'booking_history'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)

    # Status change
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Changed by
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    booking = db.relationship('Booking', back_populates='history')
    changer = db.relationship('User')

    def __repr__(self):
        return f'<BookingHistory {self.old_status} -> {self.new_status}>'
