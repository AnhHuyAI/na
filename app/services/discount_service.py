"""
Discount Service

Handles discount code validation and application
"""

from datetime import datetime
from app import db
from app.models import DiscountCode, DiscountUsage


class DiscountService:
    """Service for managing discount codes"""

    @staticmethod
    def validate_discount_code(code, subtotal):
        """
        Validate a discount code

        Args:
            code (str): Discount code
            subtotal (float): Order subtotal

        Returns:
            tuple: (bool, str, DiscountCode|None)
                - is_valid (bool)
                - message (str)
                - discount_code (DiscountCode) if valid, None otherwise
        """
        # Find discount code
        discount_code = DiscountCode.query.filter_by(code=code.upper()).first()

        if not discount_code:
            return False, "Mã giảm giá không tồn tại", None

        # Check if active
        if not discount_code.is_active:
            return False, "Mã giảm giá đã bị vô hiệu hóa", None

        # Check validity period
        now = datetime.utcnow()
        if now < discount_code.valid_from:
            return False, "Mã giảm giá chưa có hiệu lực", None

        if now > discount_code.valid_until:
            return False, "Mã giảm giá đã hết hạn", None

        # Check usage limit
        if discount_code.usage_limit is not None:
            if discount_code.used_count >= discount_code.usage_limit:
                return False, "Mã giảm giá đã hết lượt sử dụng", None

        # Check minimum order value
        if subtotal < discount_code.min_order_value:
            return False, f"Đơn hàng tối thiểu {int(discount_code.min_order_value):,}đ để sử dụng mã này", None

        # All checks passed
        discount_amount = discount_code.calculate_discount(subtotal)
        return True, f"Mã hợp lệ! Giảm {int(discount_amount):,}đ", discount_code

    @staticmethod
    def apply_discount(booking, discount_code):
        """
        Apply discount code to a booking (create usage record)

        Args:
            booking (Booking): Booking object
            discount_code (DiscountCode): Discount code object

        Returns:
            DiscountUsage: Created usage record
        """
        # Create usage record
        usage = DiscountUsage(
            discount_code_id=discount_code.id,
            booking_id=booking.id,
            discount_amount=booking.discount_amount
        )

        db.session.add(usage)
        db.session.commit()

        return usage

    @staticmethod
    def create_discount_code(code, discount_type, value, valid_from, valid_until, **kwargs):
        """
        Create a new discount code

        Args:
            code (str): Discount code (will be uppercased)
            discount_type (str): 'fixed' or 'percentage'
            value (float): Discount value
            valid_from (datetime): Valid from
            valid_until (datetime): Valid until
            **kwargs: Optional parameters
                - max_discount (float)
                - min_order_value (float)
                - usage_limit (int)
                - description (str)

        Returns:
            DiscountCode: Created discount code

        Raises:
            ValueError: If validation fails
        """
        # Validate
        if discount_type not in ['fixed', 'percentage']:
            raise ValueError("discount_type must be 'fixed' or 'percentage'")

        if value <= 0:
            raise ValueError("value must be greater than 0")

        if discount_type == 'percentage' and value > 100:
            raise ValueError("percentage value cannot exceed 100")

        if valid_from >= valid_until:
            raise ValueError("valid_from must be before valid_until")

        # Check if code already exists
        code_upper = code.upper()
        existing = DiscountCode.query.filter_by(code=code_upper).first()
        if existing:
            raise ValueError(f"Mã giảm giá '{code_upper}' đã tồn tại")

        # Create
        discount_code = DiscountCode(
            code=code_upper,
            discount_type=discount_type,
            value=value,
            valid_from=valid_from,
            valid_until=valid_until,
            max_discount=kwargs.get('max_discount'),
            min_order_value=kwargs.get('min_order_value', 0),
            usage_limit=kwargs.get('usage_limit'),
            description=kwargs.get('description'),
            is_active=True
        )

        db.session.add(discount_code)
        db.session.commit()

        return discount_code

    @staticmethod
    def deactivate_discount_code(discount_code_id):
        """
        Deactivate a discount code

        Args:
            discount_code_id (int): Discount code ID

        Returns:
            bool: Success status
        """
        discount_code = DiscountCode.query.get(discount_code_id)
        if not discount_code:
            raise ValueError("Mã giảm giá không tồn tại")

        discount_code.is_active = False
        db.session.commit()

        return True

    @staticmethod
    def get_active_discount_codes():
        """
        Get all currently active and valid discount codes

        Returns:
            list: List of DiscountCode objects
        """
        now = datetime.utcnow()

        codes = DiscountCode.query.filter(
            DiscountCode.is_active == True,
            DiscountCode.valid_from <= now,
            DiscountCode.valid_until >= now
        ).filter(
            db.or_(
                DiscountCode.usage_limit.is_(None),
                DiscountCode.used_count < DiscountCode.usage_limit
            )
        ).all()

        return codes
