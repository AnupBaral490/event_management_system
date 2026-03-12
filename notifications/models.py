from django.conf import settings
from django.db import models

from events.models import Event


class Notification(models.Model):
	class Type(models.TextChoices):
		BOOKING = 'BOOKING', 'Booking'
		PAYMENT = 'PAYMENT', 'Payment'
		REMINDER = 'REMINDER', 'Reminder'
		SYSTEM = 'SYSTEM', 'System'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
	event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
	title = models.CharField(max_length=255)
	message = models.TextField()
	notification_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']


class EmailLog(models.Model):
	to_email = models.EmailField()
	subject = models.CharField(max_length=255)
	body = models.TextField(blank=True)
	sent_at = models.DateTimeField(auto_now_add=True)
	success = models.BooleanField(default=True)

	class Meta:
		ordering = ['-sent_at']
