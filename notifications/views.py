from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListAPIView(generics.ListAPIView):
	serializer_class = NotificationSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadAPIView(generics.UpdateAPIView):
	serializer_class = NotificationSerializer
	permission_classes = [permissions.IsAuthenticated]
	lookup_field = 'id'

	def get_queryset(self):
		return Notification.objects.filter(user=self.request.user)

	def partial_update(self, request, *args, **kwargs):
		instance = self.get_object()
		instance.is_read = True
		instance.save(update_fields=['is_read'])
		return Response(self.get_serializer(instance).data)
