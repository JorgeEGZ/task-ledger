"""
Serializers for Service model.
"""

from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Service model.
    """

    business_name = serializers.CharField(source='business.name', read_only=True)
    appointments_count = serializers.SerializerMethodField(read_only=True)
    price_display = serializers.CharField(source='price', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'business', 'business_name', 'name', 'description',
            'duration', 'price', 'price_display', 'is_active',
            'appointments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'business', 'business_name', 'appointments_count', 'created_at', 'updated_at']

    def get_appointments_count(self, obj):
        return obj.get_appointments_count()


class ServiceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a service.
    """

    class Meta:
        model = Service
        fields = ['name', 'description', 'duration', 'price', 'is_active']

    def validate_name(self, value):
        """Validate service name is unique within the business."""
        request = self.context.get('request')
        business = getattr(request, 'business', None)
        if business:
            if Service.objects.filter(business=business, name=value).exists():
                raise serializers.ValidationError(
                    'A service with this name already exists for this business.'
                )
        return value

    def validate(self, attrs):
        """Validate duration and price are positive."""
        if attrs.get('duration', 0) <= 0:
            raise serializers.ValidationError({'duration': 'Duration must be greater than 0 minutes.'})
        if attrs.get('price', 0) < 0:
            raise serializers.ValidationError({'price': 'Price cannot be negative.'})
        return attrs


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a service.
    """

    class Meta:
        model = Service
        fields = ['name', 'description', 'duration', 'price', 'is_active']

    def validate_name(self, value):
        """Validate service name is unique within the business (excluding current service)."""
        request = self.context.get('request')
        business = getattr(request, 'business', None)
        if business:
            if Service.objects.filter(business=business, name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    'A service with this name already exists for this business.'
                )
        return value
