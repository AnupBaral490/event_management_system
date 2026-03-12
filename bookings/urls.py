from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingHistoryAPIView,
    BookingHistoryPageView,
    BookingViewSet,
    CouponValidateAPIView,
    TicketDetailPageView,
    TicketListAPIView,
    TicketValidationAPIView,
)

app_name = 'bookings'

router = DefaultRouter()
router.register('api/bookings', BookingViewSet, basename='bookings-api')

urlpatterns = [
    path('', include(router.urls)),
    path('history/', BookingHistoryPageView.as_view(), name='history-page'),
    path('tickets/<slug:ticket_id>/', TicketDetailPageView.as_view(), name='ticket-detail'),
    path('api/history/', BookingHistoryAPIView.as_view(), name='history'),
    path('api/coupons/validate/', CouponValidateAPIView.as_view(), name='coupon-validate'),
    path('api/tickets/', TicketListAPIView.as_view(), name='tickets'),
    path('api/tickets/validate/', TicketValidationAPIView.as_view(), name='ticket-validate'),
]
