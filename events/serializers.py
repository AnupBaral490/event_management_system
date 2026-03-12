from django.db.models import Avg
from rest_framework import serializers

from .models import Event, EventCategory, EventReview, EventTicketType


class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'description']


class EventReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = EventReview
        fields = ['id', 'event', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']


class EventTicketTypeSerializer(serializers.ModelSerializer):
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = EventTicketType
        fields = [
            'id',
            'name',
            'description',
            'price',
            'quantity',
            'available_quantity',
            'sale_start',
            'sale_end',
            'status',
            'is_active',
        ]


class EventSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    organizer_name = serializers.CharField(source='organizer.username', read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    ticket_types = EventTicketTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'organizer',
            'organizer_name',
            'category',
            'category_name',
            'title',
            'slug',
            'description',
            'poster',
            'location_name',
            'latitude',
            'longitude',
            'start_datetime',
            'end_datetime',
            'price',
            'capacity',
            'available_seats',
            'is_published',
            'is_blocked',
            'is_live_stream_enabled',
            'stream_channel',
            'stream_join_url',
            'average_rating',
            'ticket_types',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['slug', 'organizer', 'is_blocked', 'created_at', 'updated_at']

    def get_average_rating(self, obj):
        result = obj.reviews.aggregate(avg=Avg('rating')).get('avg')
        return round(result, 2) if result else None
