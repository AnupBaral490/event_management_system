from datetime import timedelta

from django.db.models import Avg
from django.utils import timezone
from django.views.generic import DetailView, ListView
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminUserRole, IsApprovedOrganizer

from .models import Event, EventCategory, EventReview
from .serializers import EventCategorySerializer, EventReviewSerializer, EventSerializer


class EventViewSet(viewsets.ModelViewSet):
	queryset = Event.objects.select_related('category', 'organizer').all()
	serializer_class = EventSerializer
	filterset_fields = ['category', 'is_published', 'is_live_stream_enabled']
	search_fields = ['title', 'description', 'location_name']
	ordering_fields = ['start_datetime', 'price', 'created_at']

	def get_permissions(self):
		if self.action in ['create', 'update', 'partial_update', 'destroy', 'organizer_events']:
			return [permissions.IsAuthenticated(), IsApprovedOrganizer()]
		if self.action in ['block_event']:
			return [permissions.IsAuthenticated(), IsAdminUserRole()]
		return [permissions.AllowAny()]

	def get_queryset(self):
		qs = super().get_queryset()
		if self.request.user.is_authenticated and self.request.user.role in ['ADMIN', 'ORGANIZER']:
			return qs
		return qs.filter(is_published=True, is_blocked=False)

	def perform_create(self, serializer):
		serializer.save(organizer=self.request.user)

	@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsApprovedOrganizer])
	def organizer_events(self, request):
		events = Event.objects.filter(organizer=request.user).order_by('-created_at')
		return Response(EventSerializer(events, many=True, context={'request': request}).data)

	@action(detail=True, methods=['post'])
	def block_event(self, request, pk=None):
		if request.user.role != 'ADMIN':
			return Response({'detail': 'Permission denied'}, status=403)
		event = self.get_object()
		event.is_blocked = True
		event.is_published = False
		event.save(update_fields=['is_blocked', 'is_published'])
		return Response({'detail': 'Event blocked successfully'})

	@action(detail=False, methods=['get'])
	def calendar(self, request):
		events = self.get_queryset().filter(start_datetime__gte=timezone.now() - timedelta(days=1))
		payload = [
			{
				'id': event.id,
				'title': event.title,
				'start': event.start_datetime.isoformat(),
				'end': event.end_datetime.isoformat(),
				'url': f'/events/{event.slug}/',
			}
			for event in events
		]
		return Response(payload)

	@action(detail=False, methods=['get'])
	def recommendations(self, request):
		if not request.user.is_authenticated:
			return Response([])
		categories = list(
			request.user.bookings.filter(status='CONFIRMED')
			.values_list('event__category_id', flat=True)
			.distinct()
		)
		qs = self.get_queryset().exclude(bookings__user=request.user)
		if categories:
			qs = qs.filter(category_id__in=categories)
		data = EventSerializer(qs.order_by('start_datetime')[:10], many=True, context={'request': request}).data
		return Response(data)


class EventCategoryViewSet(viewsets.ModelViewSet):
	queryset = EventCategory.objects.all().order_by('name')
	serializer_class = EventCategorySerializer

	def get_permissions(self):
		if self.action in ['list', 'retrieve']:
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated(), IsAdminUserRole()]


class EventReviewViewSet(viewsets.ModelViewSet):
	serializer_class = EventReviewSerializer

	def get_queryset(self):
		return EventReview.objects.select_related('event', 'user').all()

	def get_permissions(self):
		if self.action in ['list', 'retrieve']:
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class EventListPageView(ListView):
	template_name = 'events/event_list.html'
	model = Event
	context_object_name = 'events'

	def get_queryset(self):
		query = self.request.GET.get('q', '')
		qs = Event.objects.filter(is_published=True, is_blocked=False).select_related('category', 'organizer')
		if query:
			qs = qs.filter(title__icontains=query)
		return qs.order_by('start_datetime')


class EventDetailPageView(DetailView):
	template_name = 'events/event_detail.html'
	model = Event
	slug_field = 'slug'
	slug_url_kwarg = 'slug'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['reviews'] = self.object.reviews.select_related('user')[:10]
		context['avg_rating'] = self.object.reviews.aggregate(avg=Avg('rating')).get('avg')
		return context
