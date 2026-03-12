from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'booking',
            'booking_reference',
            'provider_order_id',
            'provider_payment_id',
            'provider_signature',
            'amount',
            'currency',
            'status',
            'raw_response',
            'created_at',
        ]
        read_only_fields = ['status', 'created_at']
