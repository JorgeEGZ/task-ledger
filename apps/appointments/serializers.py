"""
Serializers for Appointment model.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, AppointmentStatus
from apps.clients.serializers import ClientSerializer
from apps.services.serializers import ServiceSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    """

    client_details = ClientSerializer(source='client', read_only=True)
    service_details = ServiceSerializer(source='service', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'business', 'business_name', 'client', 'client_details',
            'service', 'service_details', 'start_time', 'end_time', 'duration_minutes',
            'status', 'status_display', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'business', 'business_name', 'duration_minutes', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validate appointment data including overlap check."""
        request = self.context.get('request')
        business = getattr(request, 'business', None)

        if not business:
            raise serializers.ValidationError({'business': 'User has no associated business.'})

        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        service = attrs.get('service')

        # Validate times
        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time.'
                })

        # Auto-calculate end_time from service if not provided
        if service and not end_time:
            from datetime import timedelta
            attrs['end_time'] = start_time + timedelta(minutes=service.duration)
            end_time = attrs['end_time']

        # Check for overlapping appointments
        if business and start_time and end_time:
            # Exclude current appointment when updating
            exclude_id = getattr(self.instance, 'id', None)
            if Appointment.objects.has_overlap(business, start_time, end_time, exclude_id):
                raise serializers.ValidationError({
                    'start_time': 'This time slot conflicts with an existing appointment.'
                })

        # Validate start_time is in the future for new appointments
        if not self.instance and start_time:
            if start_time < timezone.now():
                raise serializers.ValidationError({
                    'start_time': 'Cannot schedule appointments in the past.'
                })

        return attrs

    def create(self, validated_data):
        """
        Create an appointment safely using DB locks and trigger Celery tasks.
        """
        from django.db import transaction
        request = self.context.get('request')
        business = getattr(request, 'business', None)
        if not business:
            raise serializers.ValidationError({'business': 'User has no associated business.'})
            
        with transaction.atomic():
            # Bloqueamos la fila del negocio durante la transacción para prevenir Race Conditions
            locked_business = type(business).objects.select_for_update().get(id=business.id)
            
            # Re-verificamos la superposición dentro del entorno bloqueado
            if Appointment.objects.has_overlap(locked_business, validated_data['start_time'], validated_data['end_time']):
                raise serializers.ValidationError({'start_time': 'This time slot conflicts with an existing appointment (Double Booking Prevented).'})

            validated_data['business'] = locked_business
            appointment = super().create(validated_data)
            
        # Trigger la alerta en segundo plano sin ralentizar la respuesta web
        from apps.appointments.tasks import send_appointment_confirmation
        send_appointment_confirmation.delay(appointment.id)
        
        return appointment


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating appointments.
    """

    class Meta:
        model = Appointment
        fields = ['client', 'service', 'start_time', 'end_time', 'notes']


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating appointments.
    """

    class Meta:
        model = Appointment
        fields = ['client', 'service', 'start_time', 'end_time', 'status', 'notes']

    def validate_status(self, value):
        """Validate status transitions."""
        if self.instance:
            current_status = self.instance.status
            # Cannot change status of completed or cancelled appointments
            if current_status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
                raise serializers.ValidationError(
                    f'Cannot change status of {current_status} appointments.'
                )
        return value


class AppointmentStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating only the appointment status.
    """

    status = serializers.ChoiceField(choices=AppointmentStatus.choices)

    def validate_status(self, value):
        """Validate status transitions."""
        if self.instance:
            current_status = self.instance.status
            if current_status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
                raise serializers.ValidationError(
                    f'Cannot change status of {current_status} appointments.'
                )
        return value
