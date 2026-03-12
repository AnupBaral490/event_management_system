from django.urls import path

from .views import PaymentListAPIView, RazorpayCreateOrderAPIView, RazorpayVerifyPaymentAPIView

app_name = 'payments'

urlpatterns = [
    path('api/create-order/', RazorpayCreateOrderAPIView.as_view(), name='create-order'),
    path('api/verify/', RazorpayVerifyPaymentAPIView.as_view(), name='verify'),
    path('api/list/', PaymentListAPIView.as_view(), name='list'),
]
