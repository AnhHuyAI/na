#!/usr/bin/env python
"""
Cronjob: Check and mark late bookings

Schedule: Every hour (0 * * * *)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.services import BookingService

def main():
    app = create_app('production')

    with app.app_context():
        count = BookingService.check_late_bookings()
        print(f"Marked {count} bookings as LATE")

if __name__ == '__main__':
    main()
