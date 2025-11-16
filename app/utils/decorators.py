"""
Utility decorators for Flask routes
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """
    Decorator to require admin role

    Usage:
        @app.route('/admin/dashboard')
        @login_required
        @admin_required
        def admin_dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)  # Unauthorized

        if not current_user.is_admin():
            abort(403)  # Forbidden

        return f(*args, **kwargs)

    return decorated_function


def customer_required(f):
    """
    Decorator to require customer role

    Usage:
        @app.route('/my-bookings')
        @login_required
        @customer_required
        def my_bookings():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        if not current_user.is_customer():
            abort(403)

        return f(*args, **kwargs)

    return decorated_function
