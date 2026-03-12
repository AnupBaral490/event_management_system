from django.urls import path

from .views import MarkNotificationReadAPIView, NotificationListAPIView

app_name = 'notifications'

urlpatterns = [
    path('api/list/', NotificationListAPIView.as_view(), name='list'),
    path('api/<int:id>/read/', MarkNotificationReadAPIView.as_view(), name='read'),
]
