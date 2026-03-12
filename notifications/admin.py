from django.contrib import admin

from .models import EmailLog, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
	list_filter = ('notification_type', 'is_read')
	search_fields = ('user__username', 'title', 'message')


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
	list_display = ('to_email', 'subject', 'success', 'sent_at')
	list_filter = ('success',)
	search_fields = ('to_email', 'subject')
