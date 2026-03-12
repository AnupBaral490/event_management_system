from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import TemplateView

from bookings.models import Booking
from events.models import Event


class HomePageView(TemplateView):
	template_name = 'home.html'


class DashboardHomeView(LoginRequiredMixin, TemplateView):
	template_name = 'dashboard/home.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user

		if user.role == 'ADMIN':
			context['total_users'] = user.__class__.objects.count()
			context['total_events'] = Event.objects.count()
			context['total_bookings'] = Booking.objects.count()
			context['total_revenue'] = Booking.objects.filter(status='CONFIRMED').aggregate(
				total=Sum('total_amount')
			)['total'] or 0
		elif user.role == 'ORGANIZER':
			organizer_events = Event.objects.filter(organizer=user)
			context['total_events'] = organizer_events.count()
			context['total_bookings'] = Booking.objects.filter(event__organizer=user).count()
			context['total_revenue'] = Booking.objects.filter(
				event__organizer=user,
				status='CONFIRMED',
			).aggregate(total=Sum('total_amount'))['total'] or 0
		else:
			context['my_bookings'] = Booking.objects.filter(user=user).count()
			context['upcoming_events'] = Event.objects.filter(bookings__user=user).distinct().count()

		return context


class CalendarPageView(TemplateView):
	template_name = 'dashboard/calendar.html'


class AnalyticsPageView(LoginRequiredMixin, TemplateView):
	template_name = 'dashboard/analytics.html'
