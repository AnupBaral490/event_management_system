from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from events.models import Event, EventTicketType

from .models import Attendance, Booking, Coupon, Ticket


class BookingSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'event',
            'event_title',
            'ticket_type',
            'ticket_type_name',
            'coupon',
            'coupon_code',
            'quantity',
            'base_amount',
            'discount_amount',
            'total_amount',
            'status',
            'booking_reference',
            'created_at',
        ]
        read_only_fields = [
            'user',
            'base_amount',
            'discount_amount',
            'total_amount',
            'status',
            'booking_reference',
            'created_at',
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    ticket_type = serializers.PrimaryKeyRelatedField(
        queryset=EventTicketType.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    coupon_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Booking
        fields = ['event', 'ticket_type', 'quantity', 'coupon_code']

    def _get_coupon(self, coupon_code, user, event, base_amount):
        if not coupon_code:
            return None

        try:
            coupon = Coupon.objects.get(code=coupon_code.upper().strip())
        except Coupon.DoesNotExist as exc:
            raise serializers.ValidationError({'coupon_code': 'Invalid coupon code.'}) from exc

        if not coupon.can_be_used_now():
            raise serializers.ValidationError({'coupon_code': 'Coupon is not active at this time.'})

        if coupon.event_id and coupon.event_id != event.id:
            raise serializers.ValidationError({'coupon_code': 'Coupon is not valid for this event.'})

        if coupon.created_by_id and coupon.created_by_id != event.organizer_id:
            raise serializers.ValidationError({'coupon_code': 'Coupon is not valid for this organizer event.'})

        if base_amount < coupon.min_order_amount:
            raise serializers.ValidationError(
                {'coupon_code': f'Minimum order amount for this coupon is INR {coupon.min_order_amount}.'}
            )

        usage_queryset = Booking.objects.filter(coupon=coupon).exclude(
            status__in=[Booking.Status.CANCELLED, Booking.Status.REFUNDED]
        )
        total_uses = usage_queryset.count()
        user_uses = usage_queryset.filter(user=user).count()

        if coupon.max_total_uses is not None and total_uses >= coupon.max_total_uses:
            raise serializers.ValidationError({'coupon_code': 'Coupon usage limit reached.'})

        if coupon.max_uses_per_user is not None and user_uses >= coupon.max_uses_per_user:
            raise serializers.ValidationError({'coupon_code': 'You have already used this coupon the maximum times.'})

        return coupon

    def validate(self, attrs):
        event = attrs['event']
        qty = attrs['quantity']
        ticket_type = attrs.get('ticket_type')
        coupon_code = attrs.get('coupon_code', '').strip()
        user = self.context['request'].user

        if qty <= 0:
            raise serializers.ValidationError('Quantity should be at least 1.')

        if event.available_seats < qty:
            raise serializers.ValidationError('Not enough seats available.')

        unit_price = Decimal(event.price)
        if ticket_type:
            if ticket_type.event_id != event.id:
                raise serializers.ValidationError({'ticket_type': 'Ticket type does not belong to selected event.'})
            if ticket_type.available_quantity < qty:
                raise serializers.ValidationError({'ticket_type': 'Not enough seats available for this ticket type.'})
            if ticket_type.status != EventTicketType.SaleStatus.ACTIVE:
                raise serializers.ValidationError({'ticket_type': 'This ticket type is not on sale.'})
            now = timezone.now()
            if ticket_type.sale_start and now < ticket_type.sale_start:
                raise serializers.ValidationError({'ticket_type': 'Ticket sale has not started yet.'})
            if ticket_type.sale_end and now > ticket_type.sale_end:
                raise serializers.ValidationError({'ticket_type': 'Ticket sale has ended.'})
            unit_price = Decimal(ticket_type.price)

        base_amount = unit_price * Decimal(qty)
        coupon = self._get_coupon(coupon_code, user, event, base_amount)
        discount_amount = coupon.calculate_discount(base_amount) if coupon else Decimal('0')
        total_amount = max(base_amount - discount_amount, Decimal('0'))

        attrs['coupon'] = coupon
        attrs['base_amount'] = base_amount
        attrs['discount_amount'] = discount_amount
        attrs['total_amount'] = total_amount
        return attrs

    def create(self, validated_data):
        validated_data.pop('coupon_code', None)
        return Booking.objects.create(
            user=self.context['request'].user,
            **validated_data,
        )


class CouponValidateSerializer(serializers.Serializer):
    event = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    ticket_type = serializers.IntegerField(required=False)
    coupon_code = serializers.CharField()

    def validate(self, attrs):
        event_id = attrs['event']
        qty = attrs['quantity']
        ticket_type_id = attrs.get('ticket_type')
        coupon_code = attrs.get('coupon_code', '').strip()
        user = self.context['request'].user

        try:
            event = self.context['event_queryset'].get(id=event_id)
        except Event.DoesNotExist as exc:
            raise serializers.ValidationError({'event': 'Invalid event.'}) from exc

        ticket_type = None
        unit_price = Decimal(event.price)
        if ticket_type_id:
            try:
                ticket_type = EventTicketType.objects.get(id=ticket_type_id, event=event, is_active=True)
            except EventTicketType.DoesNotExist as exc:
                raise serializers.ValidationError({'ticket_type': 'Invalid ticket type for this event.'}) from exc
            unit_price = Decimal(ticket_type.price)

        base_amount = unit_price * Decimal(qty)
        booking_serializer = BookingCreateSerializer(context=self.context)
        coupon = booking_serializer._get_coupon(coupon_code, user, event, base_amount)
        discount_amount = coupon.calculate_discount(base_amount)
        total_amount = max(base_amount - discount_amount, Decimal('0'))

        attrs['event_obj'] = event
        attrs['ticket_type_obj'] = ticket_type
        attrs['coupon_obj'] = coupon
        attrs['base_amount'] = base_amount
        attrs['discount_amount'] = discount_amount
        attrs['total_amount'] = total_amount
        return attrs


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
    ticket_id = serializers.CharField(required=False, allow_blank=True)
    qr_payload = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        ticket_id = (attrs.get('ticket_id') or '').strip()
        qr_payload = (attrs.get('qr_payload') or '').strip()

        if not ticket_id and not qr_payload:
            raise serializers.ValidationError('Provide a ticket ID or scanned QR payload.')

        if not ticket_id and qr_payload:
            ticket_id = qr_payload.split('|', 1)[0].strip()

        if not ticket_id:
            raise serializers.ValidationError({'qr_payload': 'Unable to extract a valid ticket ID from QR payload.'})

        try:
            ticket = Ticket.objects.select_related(
                'booking',
                'booking__event',
                'booking__event__organizer',
                'booking__user',
            ).get(ticket_id=ticket_id)
        except Ticket.DoesNotExist as exc:
            raise serializers.ValidationError('Invalid ticket ID') from exc

        request_user = self.context['request'].user
        if request_user.role == 'ORGANIZER' and ticket.booking.event.organizer_id != request_user.id:
            raise serializers.ValidationError('You can only check in tickets for your own events.')
        if ticket.is_used:
            raise serializers.ValidationError('Ticket has already been used.')
        if ticket.booking.status != Booking.Status.CONFIRMED:
            raise serializers.ValidationError('Booking is not confirmed.')

        self.context['ticket'] = ticket
        attrs['ticket_id'] = ticket_id
        return attrs

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
