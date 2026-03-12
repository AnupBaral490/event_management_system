from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Attendance, Booking, Ticket


class BookingSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'event',
            'event_title',
            'quantity',
            'total_amount',
            'status',
            'booking_reference',
            'created_at',
        ]
        read_only_fields = ['user', 'total_amount', 'status', 'booking_reference', 'created_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['event', 'quantity']

    def validate(self, attrs):
        event = attrs['event']
        qty = attrs['quantity']
        if qty <= 0:
            raise serializers.ValidationError('Quantity should be at least 1.')
        if event.available_seats < qty:
            raise serializers.ValidationError('Not enough seats available.')
        return attrs

    def create(self, validated_data):
        event = validated_data['event']
        quantity = validated_data['quantity']
        total_amount = Decimal(event.price) * Decimal(quantity)
        return Booking.objects.create(
            user=self.context['request'].user,
            event=event,
            quantity=quantity,
            total_amount=total_amount,
        )


class TicketSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    event_title = serializers.CharField(source='booking.event.title', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'ticket_id',
            'booking_reference',
            'event_title',
            'qr_code',
            'is_used',
            'issued_at',
            'checked_in_at',
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    ticket_id = serializers.CharField(source='ticket.ticket_id', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'ticket', 'ticket_id', 'event', 'attendee', 'marked_by', 'marked_at']


class TicketValidationSerializer(serializers.Serializer):
    ticket_id = serializers.CharField()

    def validate_ticket_id(self, value):
        try:
            ticket = Ticket.objects.select_related('booking', 'booking__event', 'booking__user').get(ticket_id=value)
        except Ticket.DoesNotExist as exc:
            raise serializers.ValidationError('Invalid ticket ID') from exc
        if ticket.is_used:
            raise serializers.ValidationError('Ticket has already been used.')
        if ticket.booking.status != Booking.Status.CONFIRMED:
            raise serializers.ValidationError('Booking is not confirmed.')
        self.context['ticket'] = ticket
        return value

    def save(self, **kwargs):
        ticket = self.context['ticket']
        ticket.is_used = True
        ticket.checked_in_at = timezone.now()
        ticket.save(update_fields=['is_used', 'checked_in_at'])

        attendance, _ = Attendance.objects.get_or_create(
            ticket=ticket,
            defaults={
                'event': ticket.booking.event,
                'attendee': ticket.booking.user,
                'marked_by': self.context['request'].user,
            },
        )
        return attendance
