from django.db import models

from bookings.models import Booking


class Payment(models.Model):
	class Status(models.TextChoices):
		CREATED = 'CREATED', 'Created'
		SUCCESS = 'SUCCESS', 'Success'
		FAILED = 'FAILED', 'Failed'

	booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
	provider_order_id = models.CharField(max_length=255, blank=True)
	provider_payment_id = models.CharField(max_length=255, blank=True)
	provider_signature = models.CharField(max_length=500, blank=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	currency = models.CharField(max_length=10, default='INR')
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
	raw_response = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.booking.booking_reference} - {self.status}'
