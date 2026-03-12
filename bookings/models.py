import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from events.models import Event, EventTicketType


class Coupon(models.Model):
	class DiscountType(models.TextChoices):
		PERCENTAGE = 'PERCENTAGE', 'Percentage'
		FIXED = 'FIXED', 'Fixed'

	code = models.CharField(max_length=40, unique=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='created_coupons',
	)
	event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='coupons')
	description = models.CharField(max_length=255, blank=True)
	discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
	discount_value = models.DecimalField(max_digits=10, decimal_places=2)
	max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	max_total_uses = models.PositiveIntegerField(null=True, blank=True)
	max_uses_per_user = models.PositiveIntegerField(default=1)
	valid_from = models.DateTimeField(null=True, blank=True)
	valid_until = models.DateTimeField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		self.code = self.code.upper().strip()
		super().save(*args, **kwargs)

	def can_be_used_now(self):
		now = timezone.now()
		if not self.is_active:
			return False
		if self.valid_from and now < self.valid_from:
			return False
		if self.valid_until and now > self.valid_until:
			return False
		return True

	def calculate_discount(self, base_amount):
		base_amount = Decimal(base_amount)
		if self.discount_type == self.DiscountType.PERCENTAGE:
			discount = (base_amount * Decimal(self.discount_value)) / Decimal('100')
			if self.max_discount_amount is not None:
				discount = min(discount, Decimal(self.max_discount_amount))
		else:
			discount = Decimal(self.discount_value)
		return max(min(discount, base_amount), Decimal('0'))

	def __str__(self):
		return self.code


class Booking(models.Model):
	class Status(models.TextChoices):
		PENDING = 'PENDING', 'Pending'
		CONFIRMED = 'CONFIRMED', 'Confirmed'
		CANCELLED = 'CANCELLED', 'Cancelled'
		REFUNDED = 'REFUNDED', 'Refunded'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
	ticket_type = models.ForeignKey(
		EventTicketType,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='bookings',
	)
	coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
	quantity = models.PositiveIntegerField(default=1)
	base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
		if self.base_amount == 0 and self.total_amount:
			self.base_amount = self.total_amount + (self.discount_amount or Decimal('0'))
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
