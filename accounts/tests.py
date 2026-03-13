from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AdminPasswordResetAPITests(APITestCase):
	def setUp(self):
		self.admin_user = User.objects.create_user(
			username='admin1',
			password='AdminPass123!',
			role=User.Role.ADMIN,
		)
		self.target_user = User.objects.create_user(
			username='organizer1',
			password='OldPass123!',
			role=User.Role.ORGANIZER,
		)
		self.url = reverse('accounts:user-reset-password', kwargs={'id': self.target_user.id})

	def test_admin_can_reset_user_password(self):
		self.client.force_authenticate(user=self.admin_user)

		response = self.client.put(
			self.url,
			{'new_password': 'NewStrongPass123!', 'confirm_password': 'NewStrongPass123!'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.target_user.refresh_from_db()
		self.assertTrue(self.target_user.check_password('NewStrongPass123!'))

	def test_non_admin_cannot_reset_user_password(self):
		attendee = User.objects.create_user(
			username='attendee1',
			password='AttendeePass123!',
			role=User.Role.ATTENDEE,
		)
		self.client.force_authenticate(user=attendee)

		response = self.client.put(
			self.url,
			{'new_password': 'NewStrongPass123!', 'confirm_password': 'NewStrongPass123!'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
