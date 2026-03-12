from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('booking', 'status', 'amount', 'currency', 'provider_order_id', 'created_at')
	list_filter = ('status', 'currency')
	search_fields = ('booking__booking_reference', 'provider_order_id', 'provider_payment_id')
