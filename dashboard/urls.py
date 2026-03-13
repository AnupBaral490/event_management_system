from django.urls import path

from .views import (
    AnalyticsPageView,
    CalendarPageView,
    DashboardHomeView,
    OrganizerCouponDeleteView,
    OrganizerCouponManageView,
    OrganizerTicketTypeDeleteView,
    OrganizerTicketTypeManageView,
    TicketCheckInPageView,
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),
    path('calendar/', CalendarPageView.as_view(), name='calendar'),
    path('analytics/', AnalyticsPageView.as_view(), name='analytics-page'),
    path('check-in/', TicketCheckInPageView.as_view(), name='check-in'),
    path('organizer/ticket-types/', OrganizerTicketTypeManageView.as_view(), name='organizer-ticket-types'),
    path('organizer/ticket-types/<int:pk>/delete/', OrganizerTicketTypeDeleteView.as_view(), name='organizer-ticket-type-delete'),
    path('organizer/coupons/', OrganizerCouponManageView.as_view(), name='organizer-coupons'),
    path('organizer/coupons/<int:pk>/delete/', OrganizerCouponDeleteView.as_view(), name='organizer-coupon-delete'),
]
