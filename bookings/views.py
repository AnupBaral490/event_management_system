from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from accounts.permissions import IsApprovedOrganizer

from .models import Booking, Ticket
from .serializers import (
	BookingCreateSerializer,
	BookingSerializer,
	TicketSerializer,
	TicketValidationSerializer,
)
from .services import generate_ticket_qr, send_booking_confirmation_email
from notifications.services import create_notification


class BookingViewSet(viewsets.ModelViewSet):
	queryset = Booking.objects.select_related('event', 'user').all()

	def get_serializer_class(self):
		if self.action == 'create':
			return BookingCreateSerializer
		return BookingSerializer

	def get_permissions(self):
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		user = self.request.user
		if user.role == 'ADMIN':
			return self.queryset
		if user.role == 'ORGANIZER':
			return self.queryset.filter(event__organizer=user)
		return self.queryset.filter(user=user)

	@action(detail=True, methods=['post'])
	def confirm(self, request, pk=None):
		booking = self.get_object()
		booking.status = Booking.Status.CONFIRMED
		booking.save(update_fields=['status'])
		ticket, _ = Ticket.objects.get_or_create(booking=booking)
		if not ticket.qr_code:
			generate_ticket_qr(ticket)
		send_booking_confirmation_email(booking)
		create_notification(
			user=booking.user,
			title='Booking Confirmed',
			message=f'Your booking {booking.booking_reference} for {booking.event.title} is confirmed.',
			notification_type='BOOKING',
			event=booking.event,
		)
		return Response({'detail': 'Booking confirmed', 'ticket_id': ticket.ticket_id})


class BookingHistoryAPIView(generics.ListAPIView):
	serializer_class = BookingSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Booking.objects.filter(user=self.request.user).select_related('event')


class TicketListAPIView(generics.ListAPIView):
	serializer_class = TicketSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		if user.role == 'ADMIN':
			return Ticket.objects.select_related('booking', 'booking__event').all()
		return Ticket.objects.select_related('booking', 'booking__event').filter(booking__user=user)


class TicketValidationAPIView(generics.GenericAPIView):
	serializer_class = TicketValidationSerializer
	permission_classes = [permissions.IsAuthenticated, IsApprovedOrganizer]

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		attendance = serializer.save()
		return Response({'detail': 'Ticket validated', 'attendance_id': attendance.id})


class BookingHistoryPageView(LoginRequiredMixin, ListView):
	template_name = 'bookings/history.html'
	context_object_name = 'bookings'

	def get_queryset(self):
		return Booking.objects.filter(user=self.request.user).select_related('event')


class TicketDetailPageView(LoginRequiredMixin, DetailView):
	model = Ticket
	template_name = 'bookings/ticket_detail.html'
	slug_field = 'ticket_id'
	slug_url_kwarg = 'ticket_id'

	def get_queryset(self):
		qs = Ticket.objects.select_related('booking', 'booking__event', 'booking__user')
		if self.request.user.role == 'ADMIN':
			return qs
		return qs.filter(booking__user=self.request.user)
