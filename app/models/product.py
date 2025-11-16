from datetime import datetime
from app import db
import json


class Product(db.Model):
    """Product model - Contains general information about a product"""

    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Images stored as JSON array: ["img1.jpg", "img2.jpg", ...]
    images = db.Column(db.Text, nullable=True)

    # Base price (first day price)
    price_base = db.Column(db.Numeric(10, 2), nullable=False)

    # Product type: 'clothing' or 'accessory'
    product_type = db.Column(db.String(20), nullable=False, default='clothing', index=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Metrics
    view_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    category = db.relationship('Category', back_populates='products')
    inventory_items = db.relationship('InventoryItem', back_populates='product', lazy='dynamic')
    booking_items = db.relationship('BookingItem', back_populates='product', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='product', lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.name}>'

    def get_images(self):
        """Get images as list"""
        if not self.images:
            return []
        try:
            return json.loads(self.images)
        except:
            return []

    def set_images(self, images_list):
        """Set images from list"""
        self.images = json.dumps(images_list)

    def get_first_image(self):
        """Get first image or placeholder"""
        images = self.get_images()
        if images:
            return images[0]
        return 'placeholder.jpg'

    def get_available_count(self):
        """Get count of available inventory items"""
        return self.inventory_items.filter_by(status='available').count()

    def is_available(self):
        """Check if product has available inventory"""
        return self.get_available_count() > 0

    def is_clothing(self):
        """Check if product is clothing type"""
        return self.product_type == 'clothing'

    def is_accessory(self):
        """Check if product is accessory type"""
        return self.product_type == 'accessory'

    def get_average_rating(self):
        """Get average rating from reviews"""
        approved_reviews = self.reviews.filter_by(is_approved=True)
        if approved_reviews.count() == 0:
            return 0
        total = sum([r.rating for r in approved_reviews])
        return round(total / approved_reviews.count(), 1)

    def get_reviews_count(self):
        """Get count of approved reviews"""
        return self.reviews.filter_by(is_approved=True).count()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'images': self.get_images(),
            'first_image': self.get_first_image(),
            'price_base': float(self.price_base),
            'product_type': self.product_type,
            'is_active': self.is_active,
            'available_count': self.get_available_count(),
            'is_available': self.is_available(),
            'average_rating': self.get_average_rating(),
            'reviews_count': self.get_reviews_count(),
            'view_count': self.view_count
        }
