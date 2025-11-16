"""
Customer routes - Product browsing, booking, etc.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Category, Product, Booking, BookingItem, DiscountCode, Review
from app.services import PriceCalculator, BookingService, DiscountService

customer_bp = Blueprint('customer', __name__)


# =============================================================================
# HOME & PRODUCTS
# =============================================================================

@customer_bp.route('/')
def index():
    """Homepage"""
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    featured_products = Product.query.filter_by(is_active=True).order_by(Product.view_count.desc()).limit(8).all()

    return render_template('customer/index.html',
                         categories=categories,
                         featured_products=featured_products)


@customer_bp.route('/products')
def products():
    """Product listing page"""
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    product_type = request.args.get('type')
    sort = request.args.get('sort', 'newest')

    query = Product.query.filter_by(is_active=True)

    # Filter by category
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)

    # Filter by product type
    if product_type in ['clothing', 'accessory']:
        query = query.filter_by(product_type=product_type)

    # Sorting
    if sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'price_low':
        query = query.order_by(Product.price_base.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price_base.desc())
    elif sort == 'popular':
        query = query.order_by(Product.view_count.desc())

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    products = pagination.items

    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()

    return render_template('customer/products.html',
                         products=products,
                         pagination=pagination,
                         categories=categories,
                         current_category=category_slug,
                         current_type=product_type,
                         current_sort=sort)


@customer_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()

    # Increment view count
    product.view_count += 1
    db.session.commit()

    # Get approved reviews
    reviews = Review.query.filter_by(product_id=product.id, is_approved=True)\
                    .order_by(Review.created_at.desc()).limit(10).all()

    # Get related products (same category)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()

    return render_template('customer/product_detail.html',
                         product=product,
                         reviews=reviews,
                         related_products=related_products)


# =============================================================================
# CART & CHECKOUT
# =============================================================================

@customer_bp.route('/cart')
def cart():
    """Shopping cart"""
    cart_items = session.get('cart', [])
    products = []

    if cart_items:
        products = Product.query.filter(Product.id.in_(cart_items)).all()

    return render_template('customer/cart.html', products=products)


@customer_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)

    if not product.is_active:
        return jsonify({'success': False, 'message': 'Sản phẩm không còn hoạt động'}), 400

    cart = session.get('cart', [])

    if product_id in cart:
        return jsonify({'success': False, 'message': 'Sản phẩm đã có trong giỏ hàng'}), 400

    cart.append(product_id)
    session['cart'] = cart
    session.modified = True

    return jsonify({'success': True, 'message': 'Đã thêm vào giỏ hàng', 'cart_count': len(cart)})


@customer_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove product from cart"""
    cart = session.get('cart', [])

    if product_id in cart:
        cart.remove(product_id)
        session['cart'] = cart
        session.modified = True

    return jsonify({'success': True, 'cart_count': len(cart)})


@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page"""
    cart_items = session.get('cart', [])

    if not cart_items:
        flash('Giỏ hàng trống.', 'warning')
        return redirect(url_for('customer.products'))

    products = Product.query.filter(Product.id.in_(cart_items)).all()

    if request.method == 'POST':
        # Get form data
        rental_start_str = request.form.get('rental_start')
        rental_end_str = request.form.get('rental_end')
        id_card_number = request.form.get('id_card_number')
        address = request.form.get('address')
        notes = request.form.get('notes')
        discount_code_str = request.form.get('discount_code', '').strip()

        # Parse dates
        try:
            rental_start = datetime.strptime(rental_start_str, '%Y-%m-%dT%H:%M')
            rental_end = datetime.strptime(rental_end_str, '%Y-%m-%dT%H:%M')
        except:
            flash('Định dạng ngày giờ không hợp lệ.', 'danger')
            return render_template('customer/checkout.html', products=products)

        # Validate
        if not id_card_number:
            flash('Vui lòng nhập số CCCD/CMND.', 'danger')
            return render_template('customer/checkout.html', products=products)

        # Validate discount code
        discount_code = None
        if discount_code_str:
            # Calculate subtotal first to validate
            items_data = [{'product_id': p.id, 'product_name': p.name,
                          'product_type': p.product_type, 'price_base': float(p.price_base)}
                          for p in products]
            calc_temp = PriceCalculator.calculate_booking_total(items_data, rental_start, rental_end)

            is_valid, message, discount_code = DiscountService.validate_discount_code(
                discount_code_str, calc_temp['subtotal']
            )
            if not is_valid:
                flash(f'Mã giảm giá: {message}', 'warning')
                discount_code = None

        # Prepare customer info
        customer_info = {
            'full_name': current_user.full_name,
            'phone': current_user.phone,
            'email': current_user.email,
            'id_card_number': id_card_number,
            'address': address,
            'notes': notes
        }

        # Update user's ID card if not set
        if not current_user.id_card_number:
            current_user.id_card_number = id_card_number
            if address:
                current_user.address = address

        # Create booking
        try:
            booking = BookingService.create_booking(
                user=current_user,
                items=cart_items,
                rental_start=rental_start,
                rental_end=rental_end,
                customer_info=customer_info,
                discount_code=discount_code
            )

            # Clear cart
            session['cart'] = []
            session.modified = True

            flash(f'Đặt hàng thành công! Mã đơn: {booking.booking_code}', 'success')
            return redirect(url_for('customer.booking_detail', booking_id=booking.id))

        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('customer/checkout.html', products=products)

    return render_template('customer/checkout.html', products=products)


@customer_bp.route('/validate-discount', methods=['POST'])
@login_required
def validate_discount():
    """Validate discount code (AJAX)"""
    data = request.get_json()
    code = data.get('code', '').strip()
    subtotal = data.get('subtotal', 0)

    if not code:
        return jsonify({'success': False, 'message': 'Vui lòng nhập mã giảm giá'})

    is_valid, message, discount_code = DiscountService.validate_discount_code(code, subtotal)

    if is_valid:
        discount_amount = discount_code.calculate_discount(subtotal)
        return jsonify({
            'success': True,
            'message': message,
            'discount_amount': discount_amount,
            'total': subtotal - discount_amount
        })
    else:
        return jsonify({'success': False, 'message': message})


# =============================================================================
# MY BOOKINGS
# =============================================================================

@customer_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Customer's bookings"""
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    query = Booking.query.filter_by(user_id=current_user.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter.upper())

    pagination = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    bookings = pagination.items

    return render_template('customer/my_bookings.html',
                         bookings=bookings,
                         pagination=pagination,
                         status_filter=status_filter)


@customer_bp.route('/booking/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    """Booking detail"""
    booking = Booking.query.get_or_404(booking_id)

    # Check ownership
    if booking.user_id != current_user.id and not current_user.is_admin():
        flash('Bạn không có quyền xem đơn hàng này.', 'danger')
        return redirect(url_for('customer.my_bookings'))

    return render_template('customer/booking_detail.html', booking=booking)


# =============================================================================
# REVIEWS
# =============================================================================

@customer_bp.route('/review/<int:product_id>', methods=['GET', 'POST'])
@login_required
def write_review(product_id):
    """Write a review for a product"""
    product = Product.query.get_or_404(product_id)

    # Check if user has completed booking with this product
    has_rented = Booking.query.join(Booking.items).filter(
        Booking.user_id == current_user.id,
        Booking.status == 'COMPLETED',
        BookingItem.product_id == product_id
    ).first()

    if not has_rented:
        flash('Bạn chỉ có thể đánh giá sản phẩm đã thuê.', 'warning')
        return redirect(url_for('customer.product_detail', slug=product.slug))

    # Check if already reviewed
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing_review:
        flash('Bạn đã đánh giá sản phẩm này rồi.', 'info')
        return redirect(url_for('customer.product_detail', slug=product.slug))

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()

        if not rating or rating < 1 or rating > 5:
            flash('Vui lòng chọn số sao (1-5).', 'danger')
            return render_template('customer/write_review.html', product=product)

        review = Review(
            product_id=product_id,
            user_id=current_user.id,
            booking_id=has_rented.id,
            rating=rating,
            comment=comment,
            is_approved=False  # Pending admin approval
        )

        db.session.add(review)
        db.session.commit()

        flash('Cảm ơn bạn đã đánh giá! Đánh giá sẽ được hiển thị sau khi admin duyệt.', 'success')
        return redirect(url_for('customer.product_detail', slug=product.slug))

    return render_template('customer/write_review.html', product=product)
