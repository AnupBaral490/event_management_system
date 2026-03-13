from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.serializers import BookingCreateSerializer
from events.models import Event, EventCategory, EventTicketType

from .models import Attendance, Booking, Coupon, Ticket


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


class TicketCheckInTests(APITestCase):
	def setUp(self):
		self.organizer = User.objects.create_user(
			username='organizer-checkin',
			password='pass12345',
			role='ORGANIZER',
			is_organizer_approved=True,
		)
		self.other_organizer = User.objects.create_user(
			username='other-organizer',
			password='pass12345',
			role='ORGANIZER',
			is_organizer_approved=True,
		)
		self.admin = User.objects.create_user(
			username='admin-checkin',
			password='pass12345',
			role='ADMIN',
		)
		self.attendee = User.objects.create_user(
			username='attendee-checkin',
			password='pass12345',
			role='ATTENDEE',
		)
		self.category = EventCategory.objects.create(name='Music')
		self.event = Event.objects.create(
			organizer=self.organizer,
			category=self.category,
			title='Live Show',
			description='Concert',
			location_name='Arena',
			start_datetime='2030-02-10T10:00:00Z',
			end_datetime='2030-02-10T18:00:00Z',
			price=Decimal('500.00'),
			capacity=100,
			is_published=True,
		)
		self.other_event = Event.objects.create(
			organizer=self.other_organizer,
			category=self.category,
			title='Private Show',
			description='Concert',
			location_name='Club',
			start_datetime='2030-03-10T10:00:00Z',
			end_datetime='2030-03-10T18:00:00Z',
			price=Decimal('700.00'),
			capacity=80,
			is_published=True,
		)
		self.booking = Booking.objects.create(
			user=self.attendee,
			event=self.event,
			quantity=1,
			base_amount=Decimal('500.00'),
			discount_amount=Decimal('0.00'),
			total_amount=Decimal('500.00'),
			status=Booking.Status.CONFIRMED,
		)
		self.ticket = Ticket.objects.create(booking=self.booking)
		self.other_booking = Booking.objects.create(
			user=self.attendee,
			event=self.other_event,
			quantity=1,
			base_amount=Decimal('700.00'),
			discount_amount=Decimal('0.00'),
			total_amount=Decimal('700.00'),
			status=Booking.Status.CONFIRMED,
		)
		self.other_ticket = Ticket.objects.create(booking=self.other_booking)
		self.validate_url = reverse('bookings:ticket-validate')

	def test_organizer_can_validate_ticket_using_qr_payload(self):
		self.client.force_authenticate(user=self.organizer)
		payload = f'{self.ticket.ticket_id}|{self.attendee.id}|{self.event.id}'

		response = self.client.post(self.validate_url, {'qr_payload': payload}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.ticket.refresh_from_db()
		self.assertTrue(self.ticket.is_used)
		attendance = Attendance.objects.get(ticket=self.ticket)
		self.assertEqual(attendance.marked_by, self.organizer)

	def test_duplicate_ticket_scan_is_rejected(self):
		self.ticket.is_used = True
		self.ticket.save(update_fields=['is_used'])
		self.client.force_authenticate(user=self.organizer)

		response = self.client.post(self.validate_url, {'ticket_id': self.ticket.ticket_id}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('already been used', str(response.data))

	def test_organizer_cannot_validate_other_organizer_ticket(self):
		self.client.force_authenticate(user=self.organizer)

		response = self.client.post(self.validate_url, {'ticket_id': self.other_ticket.ticket_id}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('own events', str(response.data))

	def test_admin_can_validate_any_ticket(self):
		self.client.force_authenticate(user=self.admin)

		response = self.client.post(self.validate_url, {'ticket_id': self.other_ticket.ticket_id}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.other_ticket.refresh_from_db()
		self.assertTrue(self.other_ticket.is_used)
