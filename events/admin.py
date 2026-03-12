from django.contrib import admin

from .models import Event, EventCategory, EventReview


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('title', 'organizer', 'start_datetime', 'price', 'capacity', 'is_published', 'is_blocked')
	list_filter = ('is_published', 'is_blocked', 'category')
	search_fields = ('title', 'location_name', 'organizer__username')
	prepopulated_fields = {'slug': ('title',)}


@admin.register(EventReview)
class EventReviewAdmin(admin.ModelAdmin):
	list_display = ('event', 'user', 'rating', 'created_at')
	list_filter = ('rating',)
