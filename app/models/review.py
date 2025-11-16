from datetime import datetime
from app import db


class Review(db.Model):
    """Review model - Product reviews from customers"""

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)

    # Rating: 1-5 stars
    rating = db.Column(db.Integer, nullable=False)

    # Comment
    comment = db.Column(db.Text, nullable=True)

    # Approval status
    is_approved = db.Column(db.Boolean, default=False, index=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    product = db.relationship('Product', back_populates='reviews')
    user = db.relationship('User', foreign_keys=[user_id], back_populates='reviews')
    approver = db.relationship('User', foreign_keys=[approved_by])
    booking = db.relationship('Booking')

    def __repr__(self):
        return f'<Review {self.product.name if self.product else "N/A"} - {self.rating} stars>'

    def get_stars_html(self):
        """Get HTML for star rating display"""
        stars = []
        for i in range(1, 6):
            if i <= self.rating:
                stars.append('<i class="fas fa-star text-warning"></i>')
            else:
                stars.append('<i class="far fa-star text-warning"></i>')
        return ' '.join(stars)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'user_name': self.user.full_name if self.user else 'Anonymous',
            'rating': self.rating,
            'comment': self.comment,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat()
        }
