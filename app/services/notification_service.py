"""
Notification Service

Handles email notifications for bookings
"""

from flask import render_template, current_app
from flask_mail import Message
from app import mail
from threading import Thread


class NotificationService:
    """Service for sending notifications"""

    @staticmethod
    def send_async_email(app, msg):
        """Send email asynchronously"""
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                # Log error (in production, use proper logging)
                print(f"Error sending email: {e}")

    @staticmethod
    def send_email(subject, recipient, template, **kwargs):
        """
        Send an email

        Args:
            subject (str): Email subject
            recipient (str): Recipient email address
            template (str): Template name (without .html extension)
            **kwargs: Template variables
        """
        msg = Message(
            subject=f"[{current_app.config['SHOP_NAME']}] {subject}",
            recipients=[recipient],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )

        try:
            msg.html = render_template(f'emails/{template}.html', **kwargs)
        except:
            # Fallback to plain text if template doesn't exist
            msg.body = render_template(f'emails/{template}.txt', **kwargs)

        # Send asynchronously
        app = current_app._get_current_object()
        thread = Thread(target=NotificationService.send_async_email, args=(app, msg))
        thread.start()

    # =========================================================================
    # BOOKING EMAILS
    # =========================================================================

    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation email (PENDING)"""
        NotificationService.send_email(
            subject=f"Đơn thuê #{booking.booking_code} đã được tạo",
            recipient=booking.customer_email,
            template='booking_confirmation',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME'],
            shop_phone=current_app.config['SHOP_PHONE'],
            shop_email=current_app.config['SHOP_EMAIL']
        )

    @staticmethod
    def send_booking_approved(booking):
        """Send booking approved email (APPROVED)"""
        NotificationService.send_email(
            subject=f"Đơn #{booking.booking_code} đã được duyệt ✓",
            recipient=booking.customer_email,
            template='booking_approved',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME'],
            shop_address=current_app.config['SHOP_ADDRESS'],
            shop_phone=current_app.config['SHOP_PHONE']
        )

    @staticmethod
    def send_booking_rejected(booking, reason):
        """Send booking rejected email (REJECTED)"""
        NotificationService.send_email(
            subject=f"Đơn #{booking.booking_code} bị từ chối",
            recipient=booking.customer_email,
            template='booking_rejected',
            booking=booking,
            reason=reason,
            shop_name=current_app.config['SHOP_NAME'],
            shop_phone=current_app.config['SHOP_PHONE']
        )

    @staticmethod
    def send_renting_confirmation(booking):
        """Send renting confirmation email (customer picked up)"""
        NotificationService.send_email(
            subject=f"Bạn đã nhận đồ - Đơn #{booking.booking_code}",
            recipient=booking.customer_email,
            template='renting_confirmation',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME'],
            shop_phone=current_app.config['SHOP_PHONE']
        )

    @staticmethod
    def send_booking_completed(booking):
        """Send booking completed email"""
        NotificationService.send_email(
            subject=f"Cảm ơn bạn đã sử dụng dịch vụ!",
            recipient=booking.customer_email,
            template='booking_completed',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME']
        )

    @staticmethod
    def send_late_notification(booking):
        """Send late notification email"""
        NotificationService.send_email(
            subject=f"⚠️ Đơn #{booking.booking_code} đã quá hạn",
            recipient=booking.customer_email,
            template='booking_late',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME'],
            shop_phone=current_app.config['SHOP_PHONE']
        )

    # =========================================================================
    # REMINDER EMAILS
    # =========================================================================

    @staticmethod
    def send_pickup_reminder(booking):
        """Send reminder 1 day before pickup"""
        NotificationService.send_email(
            subject=f"Nhắc nhở: Nhận đồ vào ngày mai - Đơn #{booking.booking_code}",
            recipient=booking.customer_email,
            template='reminder_pickup',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME'],
            shop_address=current_app.config['SHOP_ADDRESS'],
            shop_phone=current_app.config['SHOP_PHONE']
        )

    @staticmethod
    def send_return_reminder(booking):
        """Send reminder 1 day before return"""
        NotificationService.send_email(
            subject=f"Nhắc nhở: Trả đồ vào ngày mai - Đơn #{booking.booking_code}",
            recipient=booking.customer_email,
            template='reminder_return',
            booking=booking,
            shop_name=current_app.config['SHOP_NAME'],
            shop_address=current_app.config['SHOP_ADDRESS'],
            shop_phone=current_app.config['SHOP_PHONE']
        )
