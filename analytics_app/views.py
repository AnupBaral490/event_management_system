from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from rest_framework import generics, permissions
from rest_framework.response import Response

from bookings.models import Booking


class DashboardAnalyticsAPIView(generics.GenericAPIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, *args, **kwargs):
		qs = Booking.objects.filter(status='CONFIRMED')
		if request.user.role == 'ORGANIZER':
			qs = qs.filter(event__organizer=request.user)

		totals = qs.aggregate(
			total_revenue=Sum('total_amount'),
			total_tickets=Sum('quantity'),
			total_bookings=Count('id'),
			unique_attendees=Count('user', distinct=True),
		)
		trend = (
			qs.annotate(date=TruncDate('created_at'))
			.values('date')
			.annotate(bookings=Count('id'), revenue=Sum('total_amount'))
			.order_by('date')
		)
		return Response({'totals': totals, 'trend': list(trend)})
