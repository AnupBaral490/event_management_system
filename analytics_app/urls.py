from django.urls import path

from .views import DashboardAnalyticsAPIView

app_name = 'analytics_app'

urlpatterns = [
    path('api/dashboard/', DashboardAnalyticsAPIView.as_view(), name='dashboard-api'),
]
