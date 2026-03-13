from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from bookings.models import Booking, Coupon
from bookings.serializers import TicketValidationSerializer
from events.models import Event, EventTicketType

from .forms import OrganizerCouponForm, OrganizerTicketTypeForm


class HomePageView(TemplateView):
	template_name = 'home.html'


class OrganizerOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		user = self.request.user
		return user.role == 'ORGANIZER' and user.is_organizer_approved

	def handle_no_permission(self):
		messages.error(self.request, 'Only approved organizers can access this page.')
		return redirect('dashboard:home')


class AdminOrOrganizerCheckInMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		user = self.request.user
		return user.role == 'ADMIN' or (user.role == 'ORGANIZER' and user.is_organizer_approved)

	def handle_no_permission(self):
		messages.error(self.request, 'Only admins and approved organizers can access check-in tools.')
		return redirect('dashboard:home')


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


class TicketCheckInPageView(AdminOrOrganizerCheckInMixin, TemplateView):
	template_name = 'dashboard/check_in.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		event_queryset = Event.objects.filter(is_published=True, is_blocked=False)
		if user.role == 'ORGANIZER':
			event_queryset = event_queryset.filter(organizer=user)

		context['managed_events'] = event_queryset.order_by('start_datetime')[:6]
		context['checked_in_count'] = Booking.objects.filter(
			status=Booking.Status.CONFIRMED,
			ticket__is_used=True,
			**({'event__organizer': user} if user.role == 'ORGANIZER' else {}),
		).count()
		context['pending_check_ins'] = Booking.objects.filter(
			status=Booking.Status.CONFIRMED,
			ticket__is_used=False,
			**({'event__organizer': user} if user.role == 'ORGANIZER' else {}),
		).count()
		context['validation_result'] = kwargs.get('validation_result')
		context['submitted_value'] = kwargs.get('submitted_value', '')
		return context

	def post(self, request, *args, **kwargs):
		submitted_value = (request.POST.get('ticket_input') or '').strip()
		serializer = TicketValidationSerializer(
			data={'ticket_id': submitted_value, 'qr_payload': submitted_value},
			context={'request': request},
		)

		if serializer.is_valid():
			attendance = serializer.save()
			ticket = attendance.ticket
			messages.success(request, f'{ticket.ticket_id} checked in successfully.')
			return self.render_to_response(
				self.get_context_data(
					validation_result={
						'success': True,
						'ticket_id': ticket.ticket_id,
						'attendee_name': ticket.booking.user.get_full_name() or ticket.booking.user.username,
						'event_title': ticket.booking.event.title,
						'checked_in_at': ticket.checked_in_at,
					},
				)
			)

		error_text = ' '.join(
			str(message)
			for messages_list in serializer.errors.values()
			for message in (messages_list if isinstance(messages_list, list) else [messages_list])
		)
		messages.error(request, error_text or 'Unable to validate ticket.')
		return self.render_to_response(
			self.get_context_data(
				validation_result={'success': False, 'message': error_text or 'Unable to validate ticket.'},
				submitted_value=submitted_value,
			)
		)


class OrganizerTicketTypeManageView(OrganizerOnlyMixin, TemplateView):
	template_name = 'dashboard/organizer_ticket_types.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = kwargs.get('form') or OrganizerTicketTypeForm(organizer=self.request.user)
		context['ticket_types'] = EventTicketType.objects.select_related('event').filter(
			event__organizer=self.request.user
		).order_by('event__start_datetime', 'price')
		return context

	def post(self, request, *args, **kwargs):
		form = OrganizerTicketTypeForm(request.POST, organizer=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Ticket type created successfully.')
			return redirect('dashboard:organizer-ticket-types')
		messages.error(request, 'Please fix the form errors and try again.')
		return self.render_to_response(self.get_context_data(form=form))


class OrganizerTicketTypeDeleteView(OrganizerOnlyMixin, TemplateView):
	def post(self, request, pk, *args, **kwargs):
		ticket_type = get_object_or_404(EventTicketType, id=pk, event__organizer=request.user)
		ticket_type.delete()
		messages.success(request, 'Ticket type deleted.')
		return redirect('dashboard:organizer-ticket-types')


class OrganizerCouponManageView(OrganizerOnlyMixin, TemplateView):
	template_name = 'dashboard/organizer_coupons.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = kwargs.get('form') or OrganizerCouponForm(organizer=self.request.user)
		context['coupons'] = Coupon.objects.select_related('event').filter(created_by=self.request.user).order_by('-created_at')
		return context

	def post(self, request, *args, **kwargs):
		form = OrganizerCouponForm(request.POST, organizer=request.user)
		if form.is_valid():
			coupon = form.save(commit=False)
			coupon.created_by = request.user
			coupon.save()
			messages.success(request, 'Coupon created successfully.')
			return redirect('dashboard:organizer-coupons')
		messages.error(request, 'Please fix the form errors and try again.')
		return self.render_to_response(self.get_context_data(form=form))


class OrganizerCouponDeleteView(OrganizerOnlyMixin, TemplateView):
	def post(self, request, pk, *args, **kwargs):
		coupon = get_object_or_404(Coupon, id=pk, created_by=request.user)
		coupon.delete()
		messages.success(request, 'Coupon deleted.')
		return redirect('dashboard:organizer-coupons')
