"""
Initialize database and add sample data
"""

from app import create_app, db
from app.models import (User, Category, Product, InventoryItem,
                       Booking, BookingItem, DiscountCode)
from datetime import datetime, timedelta
import json

def init_db():
    """Initialize database and add sample data"""
    app = create_app('development')

    with app.app_context():
        # Drop all tables and recreate
        print("Dropping all tables...")
        db.drop_all()

        print("Creating all tables...")
        db.create_all()

        # =====================================================================
        # USERS
        # =====================================================================
        print("\nCreating users...")

        # Admin user
        admin = User(
            email='admin@example.com',
            full_name='Admin',
            phone='0901234567',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Customer users
        customer1 = User(
            email='customer1@example.com',
            full_name='Nguyễn Văn A',
            phone='0912345678',
            id_card_number='001099001234',
            address='123 Đường ABC, Quận 1, TP.HCM',
            role='customer',
            is_active=True
        )
        customer1.set_password('customer123')
        db.session.add(customer1)

        customer2 = User(
            email='customer2@example.com',
            full_name='Trần Thị B',
            phone='0923456789',
            id_card_number='001099005678',
            address='456 Đường XYZ, Quận 2, TP.HCM',
            role='customer',
            is_active=True
        )
        customer2.set_password('customer123')
        db.session.add(customer2)

        db.session.commit()
        print(f"✓ Created {User.query.count()} users")

        # =====================================================================
        # CATEGORIES
        # =====================================================================
        print("\nCreating categories...")

        categories_data = [
            {'name': 'Vest', 'slug': 'vest', 'description': 'Vest nam/nữ cao cấp', 'display_order': 1},
            {'name': 'Áo dài', 'slug': 'ao-dai', 'description': 'Áo dài truyền thống Việt Nam', 'display_order': 2},
            {'name': 'Đồ cưới', 'slug': 'do-cuoi', 'description': 'Trang phục cưới hỏi', 'display_order': 3},
            {'name': 'Đồ dự tiệc', 'slug': 'do-du-tiec', 'description': 'Trang phục dự tiệc', 'display_order': 4},
            {'name': 'Phụ kiện', 'slug': 'phu-kien', 'description': 'Giày, cà vạt, túi xách...', 'display_order': 5},
        ]

        categories = {}
        for data in categories_data:
            cat = Category(**data, is_active=True)
            db.session.add(cat)
            categories[data['slug']] = cat

        db.session.commit()
        print(f"✓ Created {Category.query.count()} categories")

        # =====================================================================
        # PRODUCTS
        # =====================================================================
        print("\nCreating products...")

        products_data = [
            # Vests
            {'category': 'vest', 'name': 'Vest đen cao cấp', 'slug': 'vest-den-cao-cap',
             'price_base': 200000, 'product_type': 'clothing',
             'description': 'Vest đen cao cấp, chất liệu wool, phù hợp sự kiện trang trọng'},
            {'category': 'vest', 'name': 'Vest xám hiện đại', 'slug': 'vest-xam-hien-dai',
             'price_base': 180000, 'product_type': 'clothing',
             'description': 'Vest xám slim fit, phong cách hiện đại'},

            # Áo dài
            {'category': 'ao-dai', 'name': 'Áo dài đỏ truyền thống', 'slug': 'ao-dai-do-truyen-thong',
             'price_base': 150000, 'product_type': 'clothing',
             'description': 'Áo dài đỏ truyền thống, vải lụa cao cấp'},
            {'category': 'ao-dai', 'name': 'Áo dài xanh nhạt', 'slug': 'ao-dai-xanh-nhat',
             'price_base': 150000, 'product_type': 'clothing',
             'description': 'Áo dài xanh nhạt thanh lịch'},

            # Đồ cưới
            {'category': 'do-cuoi', 'name': 'Váy cưới Princessa', 'slug': 'vay-cuoi-princessa',
             'price_base': 500000, 'product_type': 'clothing',
             'description': 'Váy cưới kiểu công chúa, đính ren và đá'},
            {'category': 'do-cuoi', 'name': 'Suit cưới nam', 'slug': 'suit-cuoi-nam',
             'price_base': 300000, 'product_type': 'clothing',
             'description': 'Suit cưới nam trắng thanh lịch'},

            # Phụ kiện
            {'category': 'phu-kien', 'name': 'Giày tây đen', 'slug': 'giay-tay-den',
             'price_base': 50000, 'product_type': 'accessory',
             'description': 'Giày tây đen bóng, size 38-44'},
            {'category': 'phu-kien', 'name': 'Cà vạt lụa', 'slug': 'ca-vat-lua',
             'price_base': 30000, 'product_type': 'accessory',
             'description': 'Cà vạt lụa cao cấp, nhiều màu'},
            {'category': 'phu-kien', 'name': 'Túi xách nữ', 'slug': 'tui-xach-nu',
             'price_base': 40000, 'product_type': 'accessory',
             'description': 'Túi xách nữ cao cấp'},
        ]

        products = {}
        for data in products_data:
            cat_slug = data.pop('category')
            data['category_id'] = categories[cat_slug].id
            data['images'] = json.dumps(['placeholder.jpg'])  # Placeholder image

            prod = Product(**data, is_active=True)
            db.session.add(prod)
            products[data['slug']] = prod

        db.session.commit()
        print(f"✓ Created {Product.query.count()} products")

        # =====================================================================
        # INVENTORY ITEMS
        # =====================================================================
        print("\nCreating inventory items...")

        inventory_data = [
            # Vest đen - 5 bộ
            ('vest-den-cao-cap', 'VEST-D-001', 'M', 'available'),
            ('vest-den-cao-cap', 'VEST-D-002', 'M', 'available'),
            ('vest-den-cao-cap', 'VEST-D-003', 'L', 'available'),
            ('vest-den-cao-cap', 'VEST-D-004', 'L', 'available'),
            ('vest-den-cao-cap', 'VEST-D-005', 'XL', 'maintenance'),

            # Vest xám - 3 bộ
            ('vest-xam-hien-dai', 'VEST-X-001', 'M', 'available'),
            ('vest-xam-hien-dai', 'VEST-X-002', 'L', 'available'),
            ('vest-xam-hien-dai', 'VEST-X-003', 'L', 'rented'),

            # Áo dài đỏ - 4 bộ
            ('ao-dai-do-truyen-thong', 'AD-D-001', 'M', 'available'),
            ('ao-dai-do-truyen-thong', 'AD-D-002', 'M', 'available'),
            ('ao-dai-do-truyen-thong', 'AD-D-003', 'L', 'available'),
            ('ao-dai-do-truyen-thong', 'AD-D-004', 'L', 'available'),

            # Giày tây - 10 đôi
            ('giay-tay-den', 'SHOE-001', '40', 'available'),
            ('giay-tay-den', 'SHOE-002', '40', 'available'),
            ('giay-tay-den', 'SHOE-003', '41', 'available'),
            ('giay-tay-den', 'SHOE-004', '42', 'available'),
            ('giay-tay-den', 'SHOE-005', '43', 'available'),

            # Cà vạt - 20 chiếc
            ('ca-vat-lua', 'TIE-001', None, 'available'),
            ('ca-vat-lua', 'TIE-002', None, 'available'),
            ('ca-vat-lua', 'TIE-003', None, 'available'),
            ('ca-vat-lua', 'TIE-004', None, 'available'),
            ('ca-vat-lua', 'TIE-005', None, 'available'),
        ]

        for prod_slug, item_code, size, status in inventory_data:
            item = InventoryItem(
                product_id=products[prod_slug].id,
                item_code=item_code,
                size=size,
                status=status
            )
            db.session.add(item)

        db.session.commit()
        print(f"✓ Created {InventoryItem.query.count()} inventory items")

        # =====================================================================
        # DISCOUNT CODES
        # =====================================================================
        print("\nCreating discount codes...")

        now = datetime.utcnow()

        discounts_data = [
            {
                'code': 'SALE50',
                'discount_type': 'fixed',
                'value': 50000,
                'min_order_value': 0,
                'usage_limit': 100,
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'description': 'Giảm 50k cho mọi đơn hàng'
            },
            {
                'code': 'NEWYEAR2025',
                'discount_type': 'percentage',
                'value': 15,
                'max_discount': 100000,
                'min_order_value': 500000,
                'usage_limit': 50,
                'valid_from': now,
                'valid_until': now + timedelta(days=30),
                'description': 'Giảm 15% (tối đa 100k) cho đơn từ 500k'
            },
            {
                'code': 'VIP10',
                'discount_type': 'percentage',
                'value': 10,
                'min_order_value': 300000,
                'usage_limit': None,  # Unlimited
                'valid_from': now,
                'valid_until': now + timedelta(days=365),
                'description': 'Giảm 10% cho khách VIP'
            },
        ]

        for data in discounts_data:
            discount = DiscountCode(**data, is_active=True)
            db.session.add(discount)

        db.session.commit()
        print(f"✓ Created {DiscountCode.query.count()} discount codes")

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "="*60)
        print("DATABASE INITIALIZED SUCCESSFULLY!")
        print("="*60)
        print(f"Users: {User.query.count()}")
        print(f"  - Admin: admin@example.com / admin123")
        print(f"  - Customer: customer1@example.com / customer123")
        print(f"Categories: {Category.query.count()}")
        print(f"Products: {Product.query.count()}")
        print(f"Inventory Items: {InventoryItem.query.count()}")
        print(f"Discount Codes: {DiscountCode.query.count()}")
        print("="*60)

if __name__ == '__main__':
    init_db()
