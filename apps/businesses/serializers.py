"""
Serializers for Business model.
"""

from rest_framework import serializers
from .models import Business


class BusinessListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing businesses.
    """

    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    clients_count = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'phone', 'address', 'owner_name',
            'is_active', 'clients_count', 'services_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner_name', 'clients_count', 'services_count']

    def get_clients_count(self, obj):
        return obj.get_clients_count()

    def get_services_count(self, obj):
        return obj.get_services_count()


class BusinessSerializer(serializers.ModelSerializer):
    """
    Full serializer for Business model.
    """

    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    clients_count = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()
    appointments_count = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'phone', 'address', 'description', 'owner', 'owner_name',
            'is_active', 'clients_count', 'services_count', 'appointments_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'owner_name', 'clients_count', 'services_count', 'appointments_count']

    def get_clients_count(self, obj):
        return obj.get_clients_count()

    def get_services_count(self, obj):
        return obj.get_services_count()

    def get_appointments_count(self, obj):
        return obj.get_appointments_count()

    def create(self, validated_data):
        """
        Create a business. Owner is set from the request context.
        """
        request = self.context.get('request')
        if request:
            validated_data['owner'] = request.user
        return super().create(validated_data)


class BusinessUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating business information.
    """

    class Meta:
        model = Business
        fields = ['name', 'phone', 'address', 'description', 'is_active']
