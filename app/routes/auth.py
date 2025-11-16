"""
Authentication routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Tài khoản đã bị vô hiệu hóa.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            flash(f'Chào mừng {user.full_name}!', 'success')

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('customer.index'))
        else:
            flash('Email hoặc mật khẩu không đúng.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for('customer.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        # Validation
        if not all([email, password, confirm_password, full_name, phone]):
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'danger')
            return render_template('auth/register.html')

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'danger')
            return render_template('auth/register.html')

        # Create user
        user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            role='customer'
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('customer.index'))
