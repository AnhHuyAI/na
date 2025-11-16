#!/usr/bin/env python
"""
Cronjob: Auto-complete bookings that have been in RETURNED_CLEANING for too long

If a booking has been RETURNED_CLEANING for more than X days (configurable),
automatically mark it as COMPLETED and set inventory items to available.

Schedule: Daily at 00:00 (0 0 * * *)
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Booking, InventoryItem, BookingHistory
from app.services import NotificationService
from flask import current_app

def main():
    app = create_app('production')

    with app.app_context():
        # Get config (default: 3 days)
        auto_complete_days = app.config.get('AUTO_COMPLETE_CLEANING_DAYS', 3)
        cutoff_date = datetime.utcnow() - timedelta(days=auto_complete_days)

        # Find bookings in RETURNED_CLEANING status for more than X days
        bookings = Booking.query.filter(
            Booking.status == 'RETURNED_CLEANING',
            Booking.updated_at < cutoff_date
        ).all()

        count = 0
        for booking in bookings:
            # Mark as completed
            booking.status = 'COMPLETED'

            # Mark all inventory items as available
            for item in booking.items:
                if item.inventory_item:
                    item.inventory_item.mark_as_available()

            # Add history
            history = BookingHistory(
                booking_id=booking.id,
                old_status='RETURNED_CLEANING',
                new_status='COMPLETED',
                notes=f'Tự động hoàn thành sau {auto_complete_days} ngày giặt'
            )
            db.session.add(history)

            # Send completion email
            NotificationService.send_booking_completed(booking)

            print(f"Auto-completed booking {booking.booking_code}")
            count += 1

        if count > 0:
            db.session.commit()

        print(f"Auto-completed {count} bookings")

if __name__ == '__main__':
    main()
