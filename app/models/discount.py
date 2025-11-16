from datetime import datetime
from app import db


class DiscountCode(db.Model):
    """Discount code model"""

    __tablename__ = 'discount_codes'

    id = db.Column(db.Integer, primary_key=True)

    # Code (e.g., SALE50, NEWYEAR2025)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Type: 'fixed' or 'percentage'
    discount_type = db.Column(db.String(20), nullable=False)

    # Value
    # If fixed: amount in VND (e.g., 50000)
    # If percentage: percentage (e.g., 10 = 10%)
    value = db.Column(db.Numeric(10, 2), nullable=False)

    # For percentage type: max discount amount
    max_discount = db.Column(db.Numeric(10, 2), nullable=True)

    # Conditions
    min_order_value = db.Column(db.Numeric(10, 2), default=0)  # Minimum order to apply

    # Usage limits
    usage_limit = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    used_count = db.Column(db.Integer, default=0)

    # Validity period
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Description
    description = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    bookings = db.relationship('Booking', back_populates='discount_code', lazy='dynamic')
    usage_records = db.relationship('DiscountUsage', back_populates='discount_code', lazy='dynamic')

    def __repr__(self):
        return f'<DiscountCode {self.code}>'

    def is_valid(self):
        """Check if discount code is currently valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )

    def can_be_used(self, order_value):
        """Check if discount can be applied to an order"""
        if not self.is_valid():
            return False, "Mã giảm giá không còn hiệu lực"

        if order_value < self.min_order_value:
            return False, f"Đơn hàng tối thiểu {int(self.min_order_value):,}đ để sử dụng mã này"

        return True, "OK"

    def calculate_discount(self, subtotal):
        """Calculate discount amount for a given subtotal"""
        if self.discount_type == 'fixed':
            return min(float(self.value), float(subtotal))
        else:  # percentage
            discount = float(subtotal) * (float(self.value) / 100)
            if self.max_discount:
                discount = min(discount, float(self.max_discount))
            return discount

    def increment_usage(self):
        """Increment usage count"""
        self.used_count += 1

    def get_display_value(self):
        """Get human-readable discount value"""
        if self.discount_type == 'fixed':
            return f"{int(self.value):,}đ"
        else:
            return f"{int(self.value)}%"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'discount_type': self.discount_type,
            'value': float(self.value),
            'max_discount': float(self.max_discount) if self.max_discount else None,
            'min_order_value': float(self.min_order_value),
            'usage_limit': self.usage_limit,
            'used_count': self.used_count,
            'valid_from': self.valid_from.isoformat(),
            'valid_until': self.valid_until.isoformat(),
            'is_active': self.is_active,
            'is_valid': self.is_valid(),
            'display_value': self.get_display_value()
        }


class DiscountUsage(db.Model):
    """Discount usage tracking model"""

    __tablename__ = 'discount_usage'

    id = db.Column(db.Integer, primary_key=True)
    discount_code_id = db.Column(db.Integer, db.ForeignKey('discount_codes.id', ondelete='CASCADE'), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)

    # Amount discounted
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    discount_code = db.relationship('DiscountCode', back_populates='usage_records')
    booking = db.relationship('Booking')

    def __repr__(self):
        return f'<DiscountUsage {self.discount_code.code} - {self.discount_amount}>'
