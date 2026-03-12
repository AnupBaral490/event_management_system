import uuid

from django.conf import settings
from django.db import models

from events.models import Event


class Booking(models.Model):
	class Status(models.TextChoices):
		PENDING = 'PENDING', 'Pending'
		CONFIRMED = 'CONFIRMED', 'Confirmed'
		CANCELLED = 'CANCELLED', 'Cancelled'
		REFUNDED = 'REFUNDED', 'Refunded'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
	quantity = models.PositiveIntegerField(default=1)
	total_amount = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	booking_reference = models.CharField(max_length=40, unique=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.booking_reference:
			self.booking_reference = f'BK-{uuid.uuid4().hex[:10].upper()}'
		super().save(*args, **kwargs)

	def __str__(self):
		return self.booking_reference


class Ticket(models.Model):
	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='ticket')
	ticket_id = models.CharField(max_length=40, unique=True, blank=True)
	qr_code = models.ImageField(upload_to='tickets/qr/', blank=True, null=True)
	is_used = models.BooleanField(default=False)
	issued_at = models.DateTimeField(auto_now_add=True)
	checked_in_at = models.DateTimeField(null=True, blank=True)

	def save(self, *args, **kwargs):
		if not self.ticket_id:
			self.ticket_id = f'TKT-{uuid.uuid4().hex[:10].upper()}'
		super().save(*args, **kwargs)

	def __str__(self):
		return self.ticket_id


class Attendance(models.Model):
	ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='attendance')
	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendances')
	attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
	marked_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='marked_attendances',
	)
	marked_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.attendee} - {self.event}'
