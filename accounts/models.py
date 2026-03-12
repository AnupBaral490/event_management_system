from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		ORGANIZER = 'ORGANIZER', 'Organizer'
		ATTENDEE = 'ATTENDEE', 'Attendee'

	role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATTENDEE)
	phone_number = models.CharField(max_length=20, blank=True)
	is_organizer_approved = models.BooleanField(default=False)

	def __str__(self):
		return f'{self.username} ({self.role})'


class OrganizerProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
	organization_name = models.CharField(max_length=255)
	about = models.TextField(blank=True)
	website = models.URLField(blank=True)
	approved_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return self.organization_name
