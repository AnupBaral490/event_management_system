from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CurrentUserRoleAPIView,
    OrganizerApprovalAPIView,
    ProfileAPIView,
    RegisterAPIView,
    UserListAPIView,
    register_page,
)

app_name = 'accounts'

urlpatterns = [
    path('register-page/', register_page, name='register-page'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('users/', UserListAPIView.as_view(), name='users'),
    path('organizers/<int:id>/approval/', OrganizerApprovalAPIView.as_view(), name='organizer-approval'),
    path('role/', CurrentUserRoleAPIView.as_view(), name='current-role'),
    path('api/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
