from django.contrib import admin

from .models import OrganizerProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ('username', 'email', 'role', 'is_organizer_approved', 'is_active')
	list_filter = ('role', 'is_organizer_approved', 'is_active')
	search_fields = ('username', 'email')


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
	list_display = ('organization_name', 'user', 'approved_at')
	search_fields = ('organization_name', 'user__username')
