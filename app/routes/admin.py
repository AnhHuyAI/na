"""
Admin routes - Booking management, inventory, reports, etc.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import (User, Category, Product, InventoryItem, Booking, BookingItem,
                       Penalty, DiscountCode, Review)
from app.services import BookingService, InventoryService, DiscountService
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__)


# =============================================================================
# DASHBOARD
# =============================================================================

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Stats
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='PENDING').count()
    renting_bookings = Booking.query.filter_by(status='RENTING').count()
    completed_bookings = Booking.query.filter_by(status='COMPLETED').count()

    total_products = Product.query.filter_by(is_active=True).count()
    total_inventory = InventoryItem.query.count()
    available_inventory = InventoryItem.query.filter_by(status='available').count()

    # Revenue this month
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    monthly_revenue = db.session.query(
        db.func.sum(Booking.total_price + Booking.penalty_amount)
    ).filter(
        Booking.status == 'COMPLETED',
        Booking.updated_at >= month_start
    ).scalar() or 0

    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()

    # Late bookings
    late_bookings = Booking.query.filter_by(status='LATE').all()

    return render_template('admin/dashboard.html',
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         renting_bookings=renting_bookings,
                         completed_bookings=completed_bookings,
                         total_products=total_products,
                         total_inventory=total_inventory,
                         available_inventory=available_inventory,
                         monthly_revenue=monthly_revenue,
                         recent_bookings=recent_bookings,
                         late_bookings=late_bookings)


# =============================================================================
# BOOKING MANAGEMENT
# =============================================================================

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    """Booking list"""
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    query = Booking.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter.upper())

    pagination = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    bookings = pagination.items

    return render_template('admin/bookings.html',
                         bookings=bookings,
                         pagination=pagination,
                         status_filter=status_filter)


@admin_bp.route('/booking/<int:booking_id>')
@login_required
@admin_required
def booking_detail(booking_id):
    """Booking detail & management"""
    booking = Booking.query.get_or_404(booking_id)

    # Get available inventory items for each product in the booking
    available_items = {}
    for item in booking.items:
        available_items[item.id] = InventoryService.get_available_items(
            item.product_id,
            booking.rental_start,
            booking.rental_end
        )

    return render_template('admin/booking_detail.html',
                         booking=booking,
                         available_items=available_items)


@admin_bp.route('/booking/<int:booking_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_booking(booking_id):
    """Approve a booking"""
    booking = Booking.query.get_or_404(booking_id)

    # Get inventory assignments from form
    assignments = {}
    for item in booking.items:
        inventory_item_id = request.form.get(f'inventory_{item.id}', type=int)
        if inventory_item_id:
            assignments[item.id] = inventory_item_id

    admin_notes = request.form.get('admin_notes', '').strip()

    try:
        BookingService.approve_booking(
            booking=booking,
            admin_user=current_user,
            inventory_assignments=assignments,
            admin_notes=admin_notes
        )
        flash(f'Đơn {booking.booking_code} đã được duyệt!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/booking/<int:booking_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_booking(booking_id):
    """Reject a booking"""
    booking = Booking.query.get_or_404(booking_id)
    reason = request.form.get('reason', '').strip()

    if not reason:
        flash('Vui lòng nhập lý do từ chối.', 'danger')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))

    try:
        BookingService.reject_booking(booking, current_user, reason)
        flash(f'Đơn {booking.booking_code} đã bị từ chối.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/booking/<int:booking_id>/mark-renting', methods=['POST'])
@login_required
@admin_required
def mark_renting(booking_id):
    """Mark booking as renting (customer picked up)"""
    booking = Booking.query.get_or_404(booking_id)

    try:
        BookingService.mark_as_renting(booking, current_user)
        flash(f'Đơn {booking.booking_code} → RENTING', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/booking/<int:booking_id>/mark-returned', methods=['POST'])
@login_required
@admin_required
def mark_returned(booking_id):
    """Mark booking as returned"""
    booking = Booking.query.get_or_404(booking_id)
    condition = request.form.get('condition', 'ok')

    try:
        if condition == 'ok':
            BookingService.mark_as_returned(booking, current_user, condition='ok')
            flash(f'Đơn {booking.booking_code} đã nhận đồ trả.', 'success')
        else:
            # Has issues - need to add penalties
            return redirect(url_for('admin.add_penalty', booking_id=booking_id))

    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/booking/<int:booking_id>/cleaning-completed', methods=['POST'])
@login_required
@admin_required
def cleaning_completed(booking_id):
    """Mark cleaning as completed"""
    booking = Booking.query.get_or_404(booking_id)

    try:
        BookingService.mark_cleaning_completed(booking, current_user)
        flash(f'Đơn {booking.booking_code} đã giặt xong → COMPLETED', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/booking/<int:booking_id>/add-penalty', methods=['GET', 'POST'])
@login_required
@admin_required
def add_penalty(booking_id):
    """Add penalty to booking"""
    booking = Booking.query.get_or_404(booking_id)

    if request.method == 'POST':
        penalty_type = request.form.get('penalty_type')
        amount = request.form.get('amount', type=float)
        reason = request.form.get('reason', '').strip()

        if not all([penalty_type, amount, reason]):
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return render_template('admin/add_penalty.html', booking=booking)

        if amount <= 0:
            flash('Số tiền phạt phải lớn hơn 0.', 'danger')
            return render_template('admin/add_penalty.html', booking=booking)

        # Create penalty
        penalty = Penalty(
            booking_id=booking.id,
            penalty_type=penalty_type,
            amount=amount,
            reason=reason,
            created_by=current_user.id
        )
        db.session.add(penalty)

        # Update booking penalty amount
        booking.penalty_amount += amount
        booking.status = 'ISSUE'

        db.session.commit()

        flash(f'Đã thêm phạt {int(amount):,}đ vào đơn {booking.booking_code}', 'success')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))

    return render_template('admin/add_penalty.html', booking=booking)


# =============================================================================
# INVENTORY MANAGEMENT
# =============================================================================

@admin_bp.route('/inventory')
@login_required
@admin_required
def inventory():
    """Inventory list"""
    product_id = request.args.get('product_id', type=int)
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    query = InventoryItem.query

    if product_id:
        query = query.filter_by(product_id=product_id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(InventoryItem.item_code).paginate(
        page=page, per_page=50, error_out=False
    )
    items = pagination.items

    products = Product.query.filter_by(is_active=True).all()

    return render_template('admin/inventory.html',
                         items=items,
                         pagination=pagination,
                         products=products,
                         status_filter=status_filter,
                         selected_product_id=product_id)


@admin_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_inventory():
    """Add new inventory item"""
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        item_code = request.form.get('item_code', '').strip().upper()
        size = request.form.get('size', '').strip()
        color = request.form.get('color', '').strip()
        condition_notes = request.form.get('condition_notes', '').strip()

        if not all([product_id, item_code]):
            flash('Vui lòng chọn sản phẩm và nhập mã bộ đồ.', 'danger')
            return redirect(url_for('admin.add_inventory'))

        try:
            item = InventoryService.create_inventory_item(
                product_id=product_id,
                item_code=item_code,
                size=size,
                color=color,
                condition_notes=condition_notes
            )
            flash(f'Đã thêm mã {item.item_code}!', 'success')
            return redirect(url_for('admin.inventory'))
        except ValueError as e:
            flash(str(e), 'danger')

    products = Product.query.filter_by(is_active=True).all()
    return render_template('admin/add_inventory.html', products=products)


@admin_bp.route('/inventory/<int:item_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_inventory_status(item_id):
    """Update inventory item status"""
    new_status = request.form.get('status')
    notes = request.form.get('notes', '').strip()

    try:
        InventoryService.update_inventory_status(item_id, new_status, notes)
        flash('Đã cập nhật trạng thái!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('admin.inventory'))


# =============================================================================
# PRODUCT MANAGEMENT
# =============================================================================

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """Product management"""
    page = request.args.get('page', 1, type=int)

    pagination = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    products = pagination.items

    return render_template('admin/products.html', products=products, pagination=pagination)


# =============================================================================
# DISCOUNT CODE MANAGEMENT
# =============================================================================

@admin_bp.route('/discounts')
@login_required
@admin_required
def discounts():
    """Discount code management"""
    codes = DiscountCode.query.order_by(DiscountCode.created_at.desc()).all()
    return render_template('admin/discounts.html', codes=codes)


@admin_bp.route('/discount/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_discount():
    """Add discount code"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        discount_type = request.form.get('discount_type')
        value = request.form.get('value', type=float)
        valid_from_str = request.form.get('valid_from')
        valid_until_str = request.form.get('valid_until')
        max_discount = request.form.get('max_discount', type=float)
        min_order_value = request.form.get('min_order_value', type=float) or 0
        usage_limit = request.form.get('usage_limit', type=int)
        description = request.form.get('description', '').strip()

        try:
            valid_from = datetime.strptime(valid_from_str, '%Y-%m-%dT%H:%M')
            valid_until = datetime.strptime(valid_until_str, '%Y-%m-%dT%H:%M')

            discount_code = DiscountService.create_discount_code(
                code=code,
                discount_type=discount_type,
                value=value,
                valid_from=valid_from,
                valid_until=valid_until,
                max_discount=max_discount,
                min_order_value=min_order_value,
                usage_limit=usage_limit,
                description=description
            )

            flash(f'Đã tạo mã giảm giá {discount_code.code}!', 'success')
            return redirect(url_for('admin.discounts'))

        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('admin/add_discount.html')


# =============================================================================
# REPORTS
# =============================================================================

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Revenue reports"""
    # Default: This month
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    completed_bookings = Booking.query.filter(
        Booking.status == 'COMPLETED',
        Booking.updated_at >= month_start
    ).all()

    total_revenue = sum(float(b.total_price) + float(b.penalty_amount) for b in completed_bookings)
    total_discount = sum(float(b.discount_amount) for b in completed_bookings)

    return render_template('admin/reports.html',
                         bookings=completed_bookings,
                         total_revenue=total_revenue,
                         total_discount=total_discount,
                         month_start=month_start)
