from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import OrganizerProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	list_display = ('username', 'email', 'role', 'is_organizer_approved', 'is_active', 'is_staff')
	list_filter = ('role', 'is_organizer_approved', 'is_active', 'is_staff', 'is_superuser')
	search_fields = ('username', 'email')
	ordering = ('username',)

	fieldsets = DjangoUserAdmin.fieldsets + (
		('Role and Profile', {'fields': ('role', 'phone_number', 'is_organizer_approved')}),
	)
	add_fieldsets = DjangoUserAdmin.add_fieldsets + (
		('Role and Profile', {'fields': ('email', 'first_name', 'last_name', 'role', 'phone_number', 'is_organizer_approved')}),
	)


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
	list_display = ('organization_name', 'user', 'approved_at')
	search_fields = ('organization_name', 'user__username')
