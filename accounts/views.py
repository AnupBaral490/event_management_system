from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.shortcuts import redirect, render
from rest_framework import generics, permissions
from rest_framework.response import Response

from .forms import UserRegistrationForm
from .permissions import IsAdminUserRole
from .serializers import OrganizerApprovalSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
	serializer_class = RegisterSerializer
	permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.RetrieveUpdateAPIView):
	serializer_class = UserSerializer

	def get_object(self):
		return self.request.user


class OrganizerApprovalAPIView(generics.UpdateAPIView):
	serializer_class = OrganizerApprovalSerializer
	permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]
	queryset = User.objects.filter(role=User.Role.ORGANIZER)
	lookup_field = 'id'


class UserListAPIView(generics.ListAPIView):
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]
	queryset = User.objects.all().order_by('-date_joined')


class CurrentUserRoleAPIView(generics.GenericAPIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, *args, **kwargs):
		return Response({'role': request.user.role, 'username': request.user.username})


def register_page(request):
	if request.method == 'POST':
		form = UserRegistrationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('dashboard:home')
	else:
		form = UserRegistrationForm()
	return render(request, 'registration/register.html', {'form': form})
