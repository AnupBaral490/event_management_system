from io import BytesIO

import qrcode
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.template.loader import render_to_string

from bookings.models import Ticket


def generate_ticket_qr(ticket: Ticket):
    qr_payload = f'{ticket.ticket_id}|{ticket.booking.user_id}|{ticket.booking.event_id}'
    qr_image = qrcode.make(qr_payload)
    buffer = BytesIO()
    qr_image.save(buffer, format='PNG')
    ticket.qr_code.save(f'{ticket.ticket_id}.png', ContentFile(buffer.getvalue()), save=True)


def send_booking_confirmation_email(booking):
    subject = f'Booking Confirmed: {booking.event.title}'
    html_message = render_to_string('emails/booking_confirmation.html', {'booking': booking})
    send_mail(
        subject=subject,
        message='Your booking has been confirmed.',
        from_email=None,
        recipient_list=[booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )
