from datetime import datetime
from app import db


class InventoryItem(db.Model):
    """Inventory item model - Physical items with unique codes"""

    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)

    # Unique item code (e.g., VEST-001, SHOE-A-123)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Status: 'available', 'rented', 'maintenance', 'lost'
    status = db.Column(db.String(20), nullable=False, default='available', index=True)

    # Metadata
    size = db.Column(db.String(20), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    condition_notes = db.Column(db.Text, nullable=True)

    # Tracking
    last_rental_id = db.Column(db.Integer, nullable=True)
    last_rental_date = db.Column(db.DateTime, nullable=True)
    total_rentals = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    product = db.relationship('Product', back_populates='inventory_items')
    booking_items = db.relationship('BookingItem', back_populates='inventory_item', lazy='dynamic')

    def __repr__(self):
        return f'<InventoryItem {self.item_code}>'

    def is_available(self):
        """Check if item is available"""
        return self.status == 'available'

    def is_rented(self):
        """Check if item is rented"""
        return self.status == 'rented'

    def is_maintenance(self):
        """Check if item is in maintenance"""
        return self.status == 'maintenance'

    def is_lost(self):
        """Check if item is lost"""
        return self.status == 'lost'

    def mark_as_rented(self, booking_id):
        """Mark item as rented"""
        self.status = 'rented'
        self.last_rental_id = booking_id
        self.last_rental_date = datetime.utcnow()
        self.total_rentals += 1

    def mark_as_available(self):
        """Mark item as available"""
        self.status = 'available'

    def mark_as_maintenance(self):
        """Mark item as maintenance"""
        self.status = 'maintenance'

    def mark_as_lost(self):
        """Mark item as lost"""
        self.status = 'lost'

    def get_rental_history(self):
        """Get rental history for this item"""
        return self.booking_items.order_by(BookingItem.id.desc()).all()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'item_code': self.item_code,
            'status': self.status,
            'size': self.size,
            'color': self.color,
            'condition_notes': self.condition_notes,
            'total_rentals': self.total_rentals,
            'last_rental_date': self.last_rental_date.isoformat() if self.last_rental_date else None,
            'created_at': self.created_at.isoformat()
        }
