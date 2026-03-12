from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from bookings.serializers import BookingCreateSerializer
from events.models import Event, EventCategory, EventTicketType

from .models import Booking, Coupon


User = get_user_model()


class BookingPricingTests(TestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.organizer = User.objects.create_user(
			username='org1',
			password='pass12345',
			role='ORGANIZER',
			is_organizer_approved=True,
		)
		self.attendee = User.objects.create_user(username='attendee1', password='pass12345', role='ATTENDEE')
		self.category = EventCategory.objects.create(name='Tech')
		self.event = Event.objects.create(
			organizer=self.organizer,
			category=self.category,
			title='DjangoConf',
			description='Conference',
			location_name='Hall A',
			start_datetime='2030-01-10T10:00:00Z',
			end_datetime='2030-01-10T18:00:00Z',
			price=Decimal('1000.00'),
			capacity=200,
			is_published=True,
		)
		self.vip = EventTicketType.objects.create(
			event=self.event,
			name='VIP',
			price=Decimal('1500.00'),
			quantity=20,
		)
		self.coupon = Coupon.objects.create(
			code='WELCOME10',
			discount_type=Coupon.DiscountType.PERCENTAGE,
			discount_value=Decimal('10.00'),
			min_order_amount=Decimal('500.00'),
			max_uses_per_user=1,
		)

	def _build_request(self):
		request = self.factory.post('/bookings/api/bookings/')
		request.user = self.attendee
		return request

	def test_booking_create_applies_ticket_type_and_coupon(self):
		serializer = BookingCreateSerializer(
			data={
				'event': self.event.id,
				'ticket_type': self.vip.id,
				'quantity': 2,
				'coupon_code': 'WELCOME10',
			},
			context={'request': self._build_request()},
		)
		self.assertTrue(serializer.is_valid(), serializer.errors)
		booking = serializer.save()

		self.assertEqual(booking.base_amount, Decimal('3000.00'))
		self.assertEqual(booking.discount_amount, Decimal('300.00'))
		self.assertEqual(booking.total_amount, Decimal('2700.00'))
		self.assertEqual(booking.ticket_type, self.vip)
		self.assertEqual(booking.coupon, self.coupon)

	def test_coupon_limit_per_user_is_enforced(self):
		Booking.objects.create(
			user=self.attendee,
			event=self.event,
			quantity=1,
			base_amount=Decimal('1000.00'),
			discount_amount=Decimal('100.00'),
			total_amount=Decimal('900.00'),
			coupon=self.coupon,
		)

		serializer = BookingCreateSerializer(
			data={
				'event': self.event.id,
				'quantity': 1,
				'coupon_code': 'WELCOME10',
			},
			context={'request': self._build_request()},
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn('coupon_code', serializer.errors)
