"""
Booking Service

Handles booking creation, updates, and status transitions
"""

from datetime import datetime
from app import db
from app.models import Booking, BookingItem, BookingHistory, InventoryItem, Product
from app.services.price_calculator import PriceCalculator
from app.services.notification_service import NotificationService


class BookingService:
    """Service for managing bookings"""

    @staticmethod
    def create_booking(user, items, rental_start, rental_end, customer_info, discount_code=None):
        """
        Create a new booking

        Args:
            user (User): User creating the booking
            items (list): List of product IDs
            rental_start (datetime): Rental start datetime
            rental_end (datetime): Rental end datetime
            customer_info (dict): Customer information
                - full_name (str)
                - phone (str)
                - email (str)
                - id_card_number (str)
                - address (str, optional)
                - notes (str, optional)
            discount_code (DiscountCode, optional): Discount code to apply

        Returns:
            Booking: Created booking object

        Raises:
            ValueError: If validation fails
        """
        # Validate dates
        if rental_start >= rental_end:
            raise ValueError("Ngày trả phải sau ngày nhận")

        if rental_start < datetime.utcnow():
            raise ValueError("Ngày nhận phải từ hiện tại trở đi")

        # Prepare items data
        items_data = []
        for product_id in items:
            product = Product.query.get(product_id)
            if not product:
                raise ValueError(f"Sản phẩm ID {product_id} không tồn tại")

            if not product.is_active:
                raise ValueError(f"Sản phẩm '{product.name}' không còn hoạt động")

            items_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_type': product.product_type,
                'price_base': float(product.price_base)
            })

        # Calculate pricing
        calculation = PriceCalculator.calculate_booking_total(
            items_data,
            rental_start,
            rental_end,
            discount_code
        )

        # Create booking
        booking = Booking(
            booking_code=Booking.generate_booking_code(),
            user_id=user.id,
            rental_start=rental_start,
            rental_end=rental_end,
            total_days=calculation['total_days'],
            subtotal=calculation['subtotal'],
            discount_amount=calculation['discount_amount'],
            total_price=calculation['total'],
            discount_code_id=discount_code.id if discount_code else None,
            status='PENDING',
            customer_name=customer_info['full_name'],
            customer_phone=customer_info['phone'],
            customer_email=customer_info['email'],
            customer_id_card=customer_info['id_card_number'],
            customer_address=customer_info.get('address'),
            customer_notes=customer_info.get('notes')
        )

        db.session.add(booking)
        db.session.flush()  # Get booking ID

        # Create booking items
        for item_calc in calculation['items']:
            booking_item = BookingItem(
                booking_id=booking.id,
                product_id=item_calc['product_id'],
                product_name=item_calc['product_name'],
                product_type=item_calc['product_type'],
                price_base=item_calc['price_base'],
                item_total=item_calc['item_total']
            )
            db.session.add(booking_item)

        # Increment discount code usage
        if discount_code:
            discount_code.increment_usage()

        # Create history record
        BookingService._add_history(booking, None, 'PENDING', 'Đơn hàng được tạo')

        db.session.commit()

        # Send confirmation email
        NotificationService.send_booking_confirmation(booking)

        return booking

    @staticmethod
    def approve_booking(booking, admin_user, inventory_assignments, admin_notes=None):
        """
        Approve a booking and assign inventory items

        Args:
            booking (Booking): Booking to approve
            admin_user (User): Admin approving the booking
            inventory_assignments (dict): Mapping of booking_item_id to inventory_item_id
                Example: {1: 5, 2: 8} means booking_item#1 gets inventory_item#5
            admin_notes (str, optional): Admin notes

        Returns:
            bool: Success status

        Raises:
            ValueError: If booking cannot be approved
        """
        if booking.status != 'PENDING':
            raise ValueError("Chỉ có thể duyệt đơn ở trạng thái PENDING")

        # Assign inventory items
        for booking_item in booking.items:
            if booking_item.id not in inventory_assignments:
                raise ValueError(f"Chưa gán mã bộ đồ cho '{booking_item.product_name}'")

            inventory_item_id = inventory_assignments[booking_item.id]
            inventory_item = InventoryItem.query.get(inventory_item_id)

            if not inventory_item:
                raise ValueError(f"Mã bộ đồ ID {inventory_item_id} không tồn tại")

            if not inventory_item.is_available():
                raise ValueError(f"Mã {inventory_item.item_code} không còn available")

            # Assign inventory item
            booking_item.inventory_item_id = inventory_item.id

            # Mark inventory as rented
            inventory_item.mark_as_rented(booking.id)

        # Update booking status
        booking.status = 'APPROVED'
        booking.approved_by = admin_user.id
        booking.approved_at = datetime.utcnow()

        if admin_notes:
            booking.admin_notes = admin_notes

        # Add history
        BookingService._add_history(
            booking,
            'PENDING',
            'APPROVED',
            f'Đơn được duyệt bởi {admin_user.full_name}',
            admin_user.id
        )

        db.session.commit()

        # Send approval email
        NotificationService.send_booking_approved(booking)

        return True

    @staticmethod
    def reject_booking(booking, admin_user, reason):
        """
        Reject a booking

        Args:
            booking (Booking): Booking to reject
            admin_user (User): Admin rejecting
            reason (str): Rejection reason

        Returns:
            bool: Success status
        """
        if booking.status != 'PENDING':
            raise ValueError("Chỉ có thể từ chối đơn ở trạng thái PENDING")

        booking.status = 'REJECTED'
        booking.rejection_reason = reason

        BookingService._add_history(
            booking,
            'PENDING',
            'REJECTED',
            f'Từ chối: {reason}',
            admin_user.id
        )

        db.session.commit()

        # Send rejection email
        NotificationService.send_booking_rejected(booking, reason)

        return True

    @staticmethod
    def mark_as_renting(booking, admin_user):
        """
        Mark booking as RENTING (customer picked up items)

        Args:
            booking (Booking): Booking
            admin_user (User): Admin confirming pickup

        Returns:
            bool: Success status
        """
        if booking.status != 'APPROVED':
            raise ValueError("Chỉ có thể chuyển sang RENTING từ APPROVED")

        booking.status = 'RENTING'

        BookingService._add_history(
            booking,
            'APPROVED',
            'RENTING',
            f'Khách đã nhận đồ - Xác nhận bởi {admin_user.full_name}',
            admin_user.id
        )

        db.session.commit()

        # Send pickup confirmation email
        NotificationService.send_renting_confirmation(booking)

        return True

    @staticmethod
    def mark_as_returned(booking, admin_user, condition='ok'):
        """
        Mark booking as returned (customer returned items)

        For CLOTHING: → RETURNED_CLEANING (needs washing)
        For ACCESSORY: → COMPLETED (no washing needed)
        For MIXED: → RETURNED_CLEANING (if any clothing exists)

        Args:
            booking (Booking): Booking
            admin_user (User): Admin confirming return
            condition (str): 'ok', 'damaged', 'lost'

        Returns:
            bool: Success status
        """
        if booking.status not in ['RENTING', 'LATE']:
            raise ValueError("Chỉ có thể chuyển sang returned từ RENTING hoặc LATE")

        # Check if booking has any clothing items
        has_clothing = any(item.product_type == 'clothing' for item in booking.items)

        if condition == 'ok':
            if has_clothing:
                # Has clothing → needs cleaning
                booking.status = 'RETURNED_CLEANING'

                # Mark clothing inventory items as maintenance
                for item in booking.items:
                    if item.product_type == 'clothing' and item.inventory_item:
                        item.inventory_item.mark_as_maintenance()

                # Mark accessory inventory items as available
                for item in booking.items:
                    if item.product_type == 'accessory' and item.inventory_item:
                        item.inventory_item.mark_as_available()

                BookingService._add_history(
                    booking,
                    booking.status,
                    'RETURNED_CLEANING',
                    f'Đã nhận đồ trả - Chờ giặt - Xác nhận bởi {admin_user.full_name}',
                    admin_user.id
                )
            else:
                # Only accessories → completed directly
                booking.status = 'COMPLETED'

                # Mark all inventory items as available
                for item in booking.items:
                    if item.inventory_item:
                        item.inventory_item.mark_as_available()

                BookingService._add_history(
                    booking,
                    booking.status,
                    'COMPLETED',
                    f'Hoàn thành - Xác nhận bởi {admin_user.full_name}',
                    admin_user.id
                )

        else:
            # Has issues → ISSUE status
            booking.status = 'ISSUE'
            BookingService._add_history(
                booking,
                booking.status,
                'ISSUE',
                f'Có vấn đề khi trả: {condition}',
                admin_user.id
            )

        db.session.commit()

        # Send appropriate email
        if booking.status == 'COMPLETED':
            NotificationService.send_booking_completed(booking)

        return True

    @staticmethod
    def mark_cleaning_completed(booking, admin_user):
        """
        Mark cleaning as completed (RETURNED_CLEANING → COMPLETED)

        Args:
            booking (Booking): Booking
            admin_user (User): Admin confirming cleaning done

        Returns:
            bool: Success status
        """
        if booking.status != 'RETURNED_CLEANING':
            raise ValueError("Chỉ áp dụng cho trạng thái RETURNED_CLEANING")

        booking.status = 'COMPLETED'

        # Mark all inventory items as available
        for item in booking.items:
            if item.inventory_item:
                item.inventory_item.mark_as_available()

        BookingService._add_history(
            booking,
            'RETURNED_CLEANING',
            'COMPLETED',
            f'Giặt xong - Hoàn thành - Xác nhận bởi {admin_user.full_name}',
            admin_user.id
        )

        db.session.commit()

        # Send completion email
        NotificationService.send_booking_completed(booking)

        return True

    @staticmethod
    def check_late_bookings():
        """
        Check and mark late bookings (cronjob)

        Returns:
            int: Number of bookings marked as late
        """
        now = datetime.utcnow()
        late_bookings = Booking.query.filter(
            Booking.status == 'RENTING',
            Booking.rental_end < now
        ).all()

        count = 0
        for booking in late_bookings:
            booking.status = 'LATE'
            BookingService._add_history(
                booking,
                'RENTING',
                'LATE',
                'Tự động: Quá hạn trả'
            )
            # Send late notification
            NotificationService.send_late_notification(booking)
            count += 1

        if count > 0:
            db.session.commit()

        return count

    @staticmethod
    def _add_history(booking, old_status, new_status, notes='', changed_by_id=None):
        """
        Add history record

        Args:
            booking (Booking): Booking
            old_status (str): Old status
            new_status (str): New status
            notes (str): Notes
            changed_by_id (int, optional): User ID who made the change
        """
        history = BookingHistory(
            booking_id=booking.id,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
            changed_by=changed_by_id
        )
        db.session.add(history)
