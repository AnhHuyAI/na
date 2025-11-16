"""
Price Calculator Service

Core logic for calculating rental prices:
- CLOTHING: Price increases progressively (special pattern)
- ACCESSORY: Fixed price per day
"""

import math
from datetime import datetime


class PriceCalculator:
    """Price calculation service"""

    @staticmethod
    def calculate_days(start_dt, end_dt):
        """
        Calculate number of days (ceiling)

        Rule: Every 24 hours = 1 day
        Less than 24 hours → Round UP to 1 day

        Args:
            start_dt (datetime): Rental start datetime
            end_dt (datetime): Rental end datetime

        Returns:
            int: Number of days (minimum 1)

        Examples:
            Start: 20/11/2025 08:00
            End:   20/11/2025 20:00 (12 hours)
            → 1 day

            Start: 20/11/2025 08:00
            End:   21/11/2025 10:00 (26 hours)
            → 2 days

            Start: 20/11/2025 07:00
            End:   23/11/2025 07:00 (72 hours)
            → 3 days
        """
        diff = end_dt - start_dt
        hours = diff.total_seconds() / 3600
        days = math.ceil(hours / 24)
        return max(days, 1)  # Minimum 1 day

    @staticmethod
    def get_clothing_increment(day_number):
        """
        Get price increment for a clothing item on a specific day

        Pattern:
        Day 1: +0k
        Day 2: +10k
        Day 3: +20k
        Day 4: +20k (same as day 3)
        Day 5: +30k
        Day 6: +30k (same as day 5)
        Day 7: +40k
        Day 8: +40k (same as day 7)
        Day 9: +50k
        Day 10: +50k (same as day 9)
        ...

        Rule: Every 2 days, increase by 10k
        Odd days and even days in same pair have same increment (except first pair)

        Args:
            day_number (int): Day number (1-indexed)

        Returns:
            float: Increment amount in VND

        Examples:
            day_number=1  → 0
            day_number=2  → 10,000
            day_number=3  → 20,000
            day_number=4  → 20,000
            day_number=5  → 30,000
            day_number=10 → 50,000
        """
        if day_number == 1:
            return 0
        elif day_number == 2:
            return 10000
        else:
            # From day 3 onwards:
            # Day 3,4: 20k (pair 2)
            # Day 5,6: 30k (pair 3)
            # Day 7,8: 40k (pair 4)
            # Day 9,10: 50k (pair 5)

            # Calculate pair index (starting from day 3)
            days_after_two = day_number - 2
            pair_index = math.ceil(days_after_two / 2)

            return (pair_index + 1) * 10000

    @staticmethod
    def calculate_clothing_price(price_base, total_days):
        """
        Calculate total price for a CLOTHING item

        Clothing price increases progressively each day

        Args:
            price_base (float): Base price (first day price)
            total_days (int): Total rental days

        Returns:
            float: Total price for all days

        Example:
            Vest - price_base: 200,000đ, total_days: 5
            Day 1: 200,000 + 0     = 200,000đ
            Day 2: 200,000 + 10,000 = 210,000đ
            Day 3: 200,000 + 20,000 = 220,000đ
            Day 4: 200,000 + 20,000 = 220,000đ
            Day 5: 200,000 + 30,000 = 230,000đ
            ────────────────────────────────────
            Total: 1,080,000đ
        """
        total = 0
        for day in range(1, total_days + 1):
            increment = PriceCalculator.get_clothing_increment(day)
            day_price = price_base + increment
            total += day_price

        return total

    @staticmethod
    def calculate_accessory_price(price_base, total_days):
        """
        Calculate total price for an ACCESSORY item

        Accessory has FIXED price per day (no progressive increase)

        Args:
            price_base (float): Base price per day
            total_days (int): Total rental days

        Returns:
            float: Total price (price_base × total_days)

        Example:
            Tie - price_base: 30,000đ, total_days: 5
            30,000đ × 5 = 150,000đ
        """
        return price_base * total_days

    @staticmethod
    def calculate_item_price(product_type, price_base, total_days):
        """
        Calculate price for a single item based on its type

        Args:
            product_type (str): 'clothing' or 'accessory'
            price_base (float): Base price
            total_days (int): Total rental days

        Returns:
            float: Total price for this item

        Raises:
            ValueError: If product_type is invalid
        """
        if product_type == 'clothing':
            return PriceCalculator.calculate_clothing_price(price_base, total_days)
        elif product_type == 'accessory':
            return PriceCalculator.calculate_accessory_price(price_base, total_days)
        else:
            raise ValueError(f"Invalid product_type: {product_type}")

    @staticmethod
    def calculate_booking_total(items, start_dt, end_dt, discount_code=None):
        """
        Calculate total for a booking (multiple items)

        Args:
            items (list): List of item dictionaries with keys:
                - product_id (int)
                - product_name (str)
                - product_type (str): 'clothing' or 'accessory'
                - price_base (float)
            start_dt (datetime): Rental start datetime
            end_dt (datetime): Rental end datetime
            discount_code (DiscountCode, optional): Discount code object

        Returns:
            dict: Calculation result with keys:
                - total_days (int)
                - items (list): List of items with calculated totals
                - subtotal (float)
                - discount_amount (float)
                - total (float)

        Example:
            items = [
                {
                    'product_id': 1,
                    'product_name': 'Vest đen cao cấp',
                    'product_type': 'clothing',
                    'price_base': 200000
                },
                {
                    'product_id': 5,
                    'product_name': 'Cà vạt lụa',
                    'product_type': 'accessory',
                    'price_base': 30000
                }
            ]
            start_dt = datetime(2025, 11, 20, 8, 0)
            end_dt = datetime(2025, 11, 24, 8, 0)
            → 4 days

            Vest: 850,000đ (clothing logic)
            Tie: 120,000đ (accessory logic)
            Subtotal: 970,000đ
            Discount: -50,000đ (if applicable)
            Total: 920,000đ
        """
        # Calculate total days
        total_days = PriceCalculator.calculate_days(start_dt, end_dt)

        # Calculate each item
        subtotal = 0
        item_details = []

        for item in items:
            item_total = PriceCalculator.calculate_item_price(
                item['product_type'],
                float(item['price_base']),
                total_days
            )

            subtotal += item_total

            item_details.append({
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'product_type': item['product_type'],
                'price_base': float(item['price_base']),
                'item_total': item_total
            })

        # Apply discount
        discount_amount = 0
        if discount_code:
            # Check if discount code can be used
            can_use, message = discount_code.can_be_used(subtotal)
            if can_use:
                discount_amount = discount_code.calculate_discount(subtotal)

        # Calculate total
        total = subtotal - discount_amount

        return {
            'total_days': total_days,
            'items': item_details,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'total': total
        }

    @staticmethod
    def get_clothing_price_breakdown(price_base, total_days):
        """
        Get detailed price breakdown for clothing (for display purposes)

        Args:
            price_base (float): Base price
            total_days (int): Total days

        Returns:
            list: List of dictionaries with day-by-day breakdown
                - day (int): Day number
                - increment (float): Increment amount
                - day_price (float): Price for this day
                - cumulative (float): Cumulative total

        Example:
            [
                {'day': 1, 'increment': 0, 'day_price': 200000, 'cumulative': 200000},
                {'day': 2, 'increment': 10000, 'day_price': 210000, 'cumulative': 410000},
                ...
            ]
        """
        breakdown = []
        cumulative = 0

        for day in range(1, total_days + 1):
            increment = PriceCalculator.get_clothing_increment(day)
            day_price = price_base + increment
            cumulative += day_price

            breakdown.append({
                'day': day,
                'increment': increment,
                'day_price': day_price,
                'cumulative': cumulative
            })

        return breakdown
