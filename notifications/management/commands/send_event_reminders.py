from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking
from notifications.services import create_notification, send_email_notification


class Command(BaseCommand):
    help = 'Send reminder notifications for events starting in next 24 hours.'

    def handle(self, *args, **options):
        now = timezone.now()
        upcoming_cutoff = now + timedelta(hours=24)

        bookings = Booking.objects.select_related('user', 'event').filter(
            status=Booking.Status.CONFIRMED,
            event__start_datetime__gte=now,
            event__start_datetime__lte=upcoming_cutoff,
        )

        sent = 0
        for booking in bookings:
            title = f'Reminder: {booking.event.title} starts soon'
            message = (
                f'Your event {booking.event.title} starts at '
                f'{booking.event.start_datetime.strftime("%Y-%m-%d %H:%M")}. '
                f'Booking reference: {booking.booking_reference}'
            )
            create_notification(booking.user, title, message, notification_type='REMINDER', event=booking.event)
            if booking.user.email:
                send_email_notification(title, message, booking.user.email)
            sent += 1

        self.stdout.write(self.style.SUCCESS(f'Reminders sent: {sent}'))
