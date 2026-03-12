from django.contrib import admin

from .models import Attendance, Booking, Coupon, Ticket


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = (
		'booking_reference',
		'user',
		'event',
		'ticket_type',
		'quantity',
		'base_amount',
		'discount_amount',
		'total_amount',
		'status',
		'created_at',
	)
	list_filter = ('status',)
	search_fields = ('booking_reference', 'user__username', 'event__title')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
	list_display = (
		'code',
		'created_by',
		'event',
		'discount_type',
		'discount_value',
		'min_order_amount',
		'max_total_uses',
		'is_active',
		'valid_from',
		'valid_until',
	)
	list_filter = ('discount_type', 'is_active')
	search_fields = ('code', 'description')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
	list_display = ('ticket_id', 'booking', 'is_used', 'issued_at')
	list_filter = ('is_used',)
	search_fields = ('ticket_id', 'booking__booking_reference')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = ('ticket', 'event', 'attendee', 'marked_by', 'marked_at')
	search_fields = ('ticket__ticket_id', 'attendee__username', 'event__title')
