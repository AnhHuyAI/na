"""
Inventory Service

Handles inventory management and availability checks
"""

from datetime import datetime
from app import db
from app.models import InventoryItem, Booking, BookingItem, Product


class InventoryService:
    """Service for managing inventory"""

    @staticmethod
    def get_available_items(product_id, start_dt, end_dt):
        """
        Get available inventory items for a product in a date range

        Args:
            product_id (int): Product ID
            start_dt (datetime): Rental start
            end_dt (datetime): Rental end

        Returns:
            list: List of available InventoryItem objects
        """
        # Get all items for this product with status 'available'
        available_items = InventoryItem.query.filter_by(
            product_id=product_id,
            status='available'
        ).all()

        # Check each item for booking conflicts
        non_conflicting_items = []

        for item in available_items:
            if not InventoryService._has_booking_conflict(item.id, start_dt, end_dt):
                non_conflicting_items.append(item)

        return non_conflicting_items

    @staticmethod
    def _has_booking_conflict(inventory_item_id, start_dt, end_dt):
        """
        Check if an inventory item has booking conflict in a date range

        Args:
            inventory_item_id (int): Inventory item ID
            start_dt (datetime): Check start
            end_dt (datetime): Check end

        Returns:
            bool: True if has conflict, False otherwise
        """
        # Find bookings that:
        # 1. Use this inventory item
        # 2. Status is APPROVED or RENTING (not completed/cancelled/rejected)
        # 3. Date ranges overlap

        conflict = BookingItem.query.join(Booking).filter(
            BookingItem.inventory_item_id == inventory_item_id,
            Booking.status.in_(['APPROVED', 'RENTING', 'LATE', 'RETURNED_CLEANING']),
            Booking.rental_start < end_dt,  # Booking starts before our end
            Booking.rental_end > start_dt    # Booking ends after our start
        ).first()

        return conflict is not None

    @staticmethod
    def check_product_availability(product_id, start_dt, end_dt, quantity=1):
        """
        Check if a product has enough available items for rental

        Args:
            product_id (int): Product ID
            start_dt (datetime): Rental start
            end_dt (datetime): Rental end
            quantity (int): Required quantity

        Returns:
            tuple: (bool, str) - (is_available, message)
        """
        product = Product.query.get(product_id)
        if not product:
            return False, "Sản phẩm không tồn tại"

        if not product.is_active:
            return False, "Sản phẩm không còn hoạt động"

        available_items = InventoryService.get_available_items(
            product_id,
            start_dt,
            end_dt
        )

        if len(available_items) >= quantity:
            return True, f"Còn {len(available_items)} bộ available"
        else:
            return False, f"Chỉ còn {len(available_items)} bộ, không đủ {quantity} bộ yêu cầu"

    @staticmethod
    def create_inventory_item(product_id, item_code, **kwargs):
        """
        Create a new inventory item

        Args:
            product_id (int): Product ID
            item_code (str): Unique item code
            **kwargs: Additional fields (size, color, condition_notes)

        Returns:
            InventoryItem: Created item

        Raises:
            ValueError: If validation fails
        """
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Sản phẩm không tồn tại")

        # Check if item_code already exists
        existing = InventoryItem.query.filter_by(item_code=item_code).first()
        if existing:
            raise ValueError(f"Mã bộ đồ '{item_code}' đã tồn tại")

        item = InventoryItem(
            product_id=product_id,
            item_code=item_code,
            status='available',
            size=kwargs.get('size'),
            color=kwargs.get('color'),
            condition_notes=kwargs.get('condition_notes')
        )

        db.session.add(item)
        db.session.commit()

        return item

    @staticmethod
    def update_inventory_status(inventory_item_id, new_status, notes=None):
        """
        Update inventory item status

        Args:
            inventory_item_id (int): Inventory item ID
            new_status (str): New status ('available', 'rented', 'maintenance', 'lost')
            notes (str, optional): Condition notes

        Returns:
            bool: Success status

        Raises:
            ValueError: If validation fails
        """
        valid_statuses = ['available', 'rented', 'maintenance', 'lost']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        item = InventoryItem.query.get(inventory_item_id)
        if not item:
            raise ValueError("Inventory item không tồn tại")

        item.status = new_status

        if notes:
            item.condition_notes = notes

        db.session.commit()

        return True

    @staticmethod
    def get_inventory_stats(product_id=None):
        """
        Get inventory statistics

        Args:
            product_id (int, optional): Filter by product ID

        Returns:
            dict: Statistics
        """
        query = InventoryItem.query

        if product_id:
            query = query.filter_by(product_id=product_id)

        all_items = query.all()

        stats = {
            'total': len(all_items),
            'available': sum(1 for item in all_items if item.status == 'available'),
            'rented': sum(1 for item in all_items if item.status == 'rented'),
            'maintenance': sum(1 for item in all_items if item.status == 'maintenance'),
            'lost': sum(1 for item in all_items if item.status == 'lost'),
            'utilization_rate': 0
        }

        # Calculate utilization rate (rented / (total - lost))
        active_total = stats['total'] - stats['lost']
        if active_total > 0:
            stats['utilization_rate'] = round((stats['rented'] / active_total) * 100, 1)

        return stats

    @staticmethod
    def get_rental_history(inventory_item_id):
        """
        Get rental history for an inventory item

        Args:
            inventory_item_id (int): Inventory item ID

        Returns:
            list: List of bookings this item was used in
        """
        booking_items = BookingItem.query.filter_by(
            inventory_item_id=inventory_item_id
        ).order_by(BookingItem.created_at.desc()).all()

        history = []
        for bi in booking_items:
            history.append({
                'booking_code': bi.booking.booking_code,
                'booking_id': bi.booking.id,
                'customer_name': bi.booking.customer_name,
                'rental_start': bi.booking.rental_start,
                'rental_end': bi.booking.rental_end,
                'status': bi.booking.status,
                'created_at': bi.booking.created_at
            })

        return history
