#!/usr/bin/env python
"""
Cronjob: Send reminder emails

- Pickup reminder: 1 day before rental_start
- Return reminder: 1 day before rental_end

Schedule: Daily at 18:00 (0 18 * * *)
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Booking
from app.services import NotificationService

def main():
    app = create_app('production')

    with app.app_context():
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)

        # Get tomorrow's date range (00:00 - 23:59)
        tomorrow_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        tomorrow_end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)

        # Send pickup reminders
        pickup_reminders = Booking.query.filter(
            Booking.status == 'APPROVED',
            Booking.rental_start >= tomorrow_start,
            Booking.rental_start <= tomorrow_end
        ).all()

        for booking in pickup_reminders:
            NotificationService.send_pickup_reminder(booking)
            print(f"Sent pickup reminder for booking {booking.booking_code}")

        # Send return reminders
        return_reminders = Booking.query.filter(
            Booking.status == 'RENTING',
            Booking.rental_end >= tomorrow_start,
            Booking.rental_end <= tomorrow_end
        ).all()

        for booking in return_reminders:
            NotificationService.send_return_reminder(booking)
            print(f"Sent return reminder for booking {booking.booking_code}")

        print(f"Total: {len(pickup_reminders)} pickup reminders, {len(return_reminders)} return reminders")

if __name__ == '__main__':
    main()
