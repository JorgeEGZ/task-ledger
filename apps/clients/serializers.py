"""
Serializers for Client model.
"""

from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """
    Serializer for Client model.
    """

    appointments_count = serializers.SerializerMethodField(read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'business', 'business_name', 'name', 'phone', 'email',
            'notes', 'is_active', 'appointments_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'business', 'business_name', 'appointments_count', 'created_at', 'updated_at']

    def get_appointments_count(self, obj):
        return obj.get_appointments_count()

    def create(self, validated_data):
        """
        Create a client. Business is set from the request context.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'business'):
            validated_data['business'] = request.business
        return super().create(validated_data)


class ClientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a client with business validation.
    """

    class Meta:
        model = Client
        fields = ['name', 'phone', 'email', 'notes', 'is_active']

    def validate_email(self, value):
        """Validate email is unique within the business."""
        if value:
            request = self.context.get('request')
            business = getattr(request, 'business', None)
            if business:
                if Client.objects.filter(business=business, email=value).exists():
                    raise serializers.ValidationError(
                        'A client with this email already exists for this business.'
                    )
        return value


class ClientUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a client.
    """

    class Meta:
        model = Client
        fields = ['name', 'phone', 'email', 'notes', 'is_active']

    def validate_email(self, value):
        """Validate email is unique within the business (excluding current client)."""
        if value:
            request = self.context.get('request')
            business = getattr(request, 'business', None)
            if business:
                if Client.objects.filter(business=business, email=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError(
                        'A client with this email already exists for this business.'
                    )
        return value
