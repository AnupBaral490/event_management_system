import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class EventCategory(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.name


class Event(models.Model):
	organizer = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='organized_events',
	)
	category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')
	title = models.CharField(max_length=255)
	slug = models.SlugField(max_length=300, unique=True, blank=True)
	description = models.TextField()
	poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)
	location_name = models.CharField(max_length=255)
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField()
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	capacity = models.PositiveIntegerField()
	is_published = models.BooleanField(default=False)
	is_blocked = models.BooleanField(default=False)
	is_live_stream_enabled = models.BooleanField(default=False)
	stream_channel = models.CharField(max_length=120, blank=True)
	stream_join_url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['start_datetime']

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(f'{self.title}-{uuid.uuid4().hex[:8]}')
		super().save(*args, **kwargs)

	@property
	def available_seats(self):
		confirmed = self.bookings.filter(status='CONFIRMED').aggregate(total=models.Sum('quantity')).get('total') or 0
		return max(self.capacity - confirmed, 0)

	def __str__(self):
		return self.title

	@property
	def has_ticket_types(self):
		return self.ticket_types.exists()

	@property
	def starting_price(self):
		if self.has_ticket_types:
			result = self.ticket_types.filter(is_active=True).aggregate(min_price=models.Min('price')).get('min_price')
			if result is not None:
				return result
		return Decimal(self.price)


class EventTicketType(models.Model):
	class SaleStatus(models.TextChoices):
		ACTIVE = 'ACTIVE', 'Active'
		INACTIVE = 'INACTIVE', 'Inactive'

	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
	name = models.CharField(max_length=120)
	description = models.CharField(max_length=255, blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	quantity = models.PositiveIntegerField()
	sale_start = models.DateTimeField(null=True, blank=True)
	sale_end = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=SaleStatus.choices, default=SaleStatus.ACTIVE)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['price', 'id']
		unique_together = ('event', 'name')

	@property
	def sold_quantity(self):
		confirmed = self.bookings.filter(status='CONFIRMED').aggregate(total=models.Sum('quantity')).get('total') or 0
		return confirmed

	@property
	def available_quantity(self):
		return max(self.quantity - self.sold_quantity, 0)

	def __str__(self):
		return f'{self.event.title} - {self.name}'


class EventReview(models.Model):
	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_reviews')
	rating = models.PositiveSmallIntegerField()
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('event', 'user')
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.event.title} - {self.rating}'
