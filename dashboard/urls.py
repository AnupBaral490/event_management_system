from django.urls import path

from .views import AnalyticsPageView, CalendarPageView, DashboardHomeView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),
    path('calendar/', CalendarPageView.as_view(), name='calendar'),
    path('analytics/', AnalyticsPageView.as_view(), name='analytics-page'),
]
