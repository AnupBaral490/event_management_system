import razorpay
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.response import Response

from bookings.models import Booking, Ticket
from bookings.services import generate_ticket_qr, send_booking_confirmation_email
from notifications.services import create_notification

from .models import Payment
from .serializers import PaymentSerializer


class RazorpayCreateOrderAPIView(generics.GenericAPIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, *args, **kwargs):
		booking_id = request.data.get('booking_id')
		booking = Booking.objects.get(id=booking_id, user=request.user)

		client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
		order_payload = {
			'amount': int(booking.total_amount * 100),
			'currency': 'INR',
			'payment_capture': 1,
		}
		order = client.order.create(data=order_payload)

		payment, _ = Payment.objects.get_or_create(
			booking=booking,
			defaults={'amount': booking.total_amount, 'provider_order_id': order['id']},
		)
		if payment.provider_order_id != order['id']:
			payment.provider_order_id = order['id']
			payment.save(update_fields=['provider_order_id'])

		return Response(
			{
				'order_id': order['id'],
				'amount': order_payload['amount'],
				'currency': 'INR',
				'key': settings.RAZORPAY_KEY_ID,
				'booking_reference': booking.booking_reference,
			}
		)


class RazorpayVerifyPaymentAPIView(generics.GenericAPIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, *args, **kwargs):
		order_id = request.data.get('razorpay_order_id')
		payment_id = request.data.get('razorpay_payment_id')
		signature = request.data.get('razorpay_signature')

		payment = Payment.objects.select_related('booking', 'booking__event', 'booking__user').get(
			provider_order_id=order_id,
			booking__user=request.user,
		)

		client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
		client.utility.verify_payment_signature(
			{
				'razorpay_order_id': order_id,
				'razorpay_payment_id': payment_id,
				'razorpay_signature': signature,
			}
		)

		payment.provider_payment_id = payment_id
		payment.provider_signature = signature
		payment.status = Payment.Status.SUCCESS
		payment.raw_response = request.data
		payment.save(update_fields=['provider_payment_id', 'provider_signature', 'status', 'raw_response'])

		booking = payment.booking
		booking.status = Booking.Status.CONFIRMED
		booking.save(update_fields=['status'])

		ticket, _ = Ticket.objects.get_or_create(booking=booking)
		if not ticket.qr_code:
			generate_ticket_qr(ticket)
		send_booking_confirmation_email(booking)
		create_notification(
			user=booking.user,
			title='Payment Successful',
			message=f'Payment completed for {booking.event.title}. Ticket {ticket.ticket_id} is ready.',
			notification_type='PAYMENT',
			event=booking.event,
		)

		return Response(
			{
				'message': 'Payment verified and booking confirmed',
				'booking_reference': booking.booking_reference,
				'ticket_id': ticket.ticket_id,
			}
		)


class PaymentListAPIView(generics.ListAPIView):
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		if self.request.user.role == 'ADMIN':
			return Payment.objects.select_related('booking', 'booking__event', 'booking__user').all()
		return Payment.objects.select_related('booking', 'booking__event', 'booking__user').filter(
			booking__user=self.request.user
		)
