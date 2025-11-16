import os
from app import create_app, db
from app.models import User, Category, Product, InventoryItem, Booking, BookingItem, Penalty, DiscountCode, Review

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Shell context for flask shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'InventoryItem': InventoryItem,
        'Booking': Booking,
        'BookingItem': BookingItem,
        'Penalty': Penalty,
        'DiscountCode': DiscountCode,
        'Review': Review
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
