from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import OrganizerProfile

User = get_user_model()


class OrganizerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerProfile
        fields = ['organization_name', 'about', 'website', 'approved_at']
        read_only_fields = ['approved_at']


class UserSerializer(serializers.ModelSerializer):
    organizer_profile = OrganizerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'role',
            'is_organizer_approved',
            'organizer_profile',
        ]
        read_only_fields = ['id', 'is_organizer_approved']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    organization_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'password',
            'role',
            'organization_name',
        ]

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError('Admin accounts cannot be self-registered.')
        return value

    def create(self, validated_data):
        organization_name = validated_data.pop('organization_name', '').strip()
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        if user.role == User.Role.ORGANIZER:
            user.is_organizer_approved = False
        user.save()

        if user.role == User.Role.ORGANIZER and organization_name:
            OrganizerProfile.objects.create(user=user, organization_name=organization_name)

        return user


class OrganizerApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_organizer_approved']

    def update(self, instance, validated_data):
        instance.is_organizer_approved = validated_data.get('is_organizer_approved', instance.is_organizer_approved)
        instance.save(update_fields=['is_organizer_approved'])
        if hasattr(instance, 'organizer_profile') and instance.is_organizer_approved:
            instance.organizer_profile.approved_at = timezone.now()
            instance.organizer_profile.save(update_fields=['approved_at'])
        return instance
