"""
Views for Appointment endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone

from common.permissions import IsBusinessOwner
from common.pagination import StandardPagination
from .models import Appointment, AppointmentStatus
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentStatusUpdateSerializer,
)


@extend_schema(tags=['Appointments'])
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments.

    Appointments are scoped to the authenticated user's business.
    Supports filtering, searching, ordering, and status management.
    """

    queryset = Appointment.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['business', 'status', 'client', 'service']
    search_fields = ['client__name', 'service__name', 'notes']
    ordering_fields = ['start_time', 'end_time', 'created_at', 'status']
    ordering = ['-start_time']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        elif self.action == 'update_status':
            return AppointmentStatusUpdateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        """
        Filter appointments to only those belonging to the current user's business.
        """
        user = self.request.user
        business = getattr(user, 'businesses', None)
        if business and business.exists():
            self.request.business = business.first()
            return Appointment.objects.filter(
                business=business.first(),
                is_deleted=False
            ).select_related('client', 'service', 'business')
        return Appointment.objects.none()

    def perform_create(self, serializer):
        """
        Set the business to the current user's business when creating an appointment.
        """
        business = getattr(self.request, 'business', None)
        if not business:
            raise serializers.ValidationError({'business': 'User has no associated business.'})
        serializer.save(business=business)

    @extend_schema(
        summary='List appointments',
        description='Retrieve all appointments for the authenticated user\'s business.',
        parameters=[
            OpenApiParameter('search', str, OpenApiParameter.QUERY, description='Search by client name, service name, or notes'),
            OpenApiParameter('status', str, OpenApiParameter.QUERY, description='Filter by status (scheduled, confirmed, completed, cancelled, no_show)'),
            OpenApiParameter('client', str, OpenApiParameter.QUERY, description='Filter by client ID'),
            OpenApiParameter('service', str, OpenApiParameter.QUERY, description='Filter by service ID'),
            OpenApiParameter('start_time_after', str, OpenApiParameter.QUERY, description='Filter appointments after this datetime'),
            OpenApiParameter('ordering', str, OpenApiParameter.QUERY, description='Order by field (start_time, end_time, created_at, etc.)'),
        ],
        responses={200: AppointmentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        # Add custom date filtering
        queryset = self.filter_queryset(self.get_queryset())
        start_time_after = request.query_params.get('start_time_after')
        if start_time_after:
            queryset = queryset.filter(start_time__gte=start_time_after)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Create appointment',
        description='Create a new appointment. Overlapping appointments are automatically prevented.',
        request=AppointmentCreateSerializer,
        responses={
            201: AppointmentSerializer,
            400: OpenApiExample('Validation Error', value={'detail': 'Error message'})
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Get appointment details',
        description='Retrieve details of a specific appointment.',
        responses={200: AppointmentSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update appointment',
        description='Update an appointment\'s information.',
        request=AppointmentUpdateSerializer,
        responses={200: AppointmentSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Delete appointment',
        description='Soft delete an appointment (marks as deleted without removing from database).',
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary='Update appointment status',
        description='Update only the status of an appointment (confirm, complete, cancel, mark no-show).',
        request=AppointmentStatusUpdateSerializer,
        responses={
            200: AppointmentSerializer,
            400: OpenApiExample('Invalid Status', value={'detail': 'Error message'})
        }
    )
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, *args, **kwargs):
        """Update the status of an appointment."""
        instance = self.get_object()
        serializer = AppointmentStatusUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(AppointmentSerializer(instance).data)

    @extend_schema(
        summary='Confirm appointment',
        description='Change appointment status to confirmed.',
        responses={200: AppointmentSerializer}
    )
    @action(detail=True, methods=['patch'])
    def confirm(self, request, *args, **kwargs):
        """Confirm an appointment."""
        instance = self.get_object()
        instance.confirm()
        return Response(AppointmentSerializer(instance).data)

    @extend_schema(
        summary='Complete appointment',
        description='Change appointment status to completed.',
        responses={200: AppointmentSerializer}
    )
    @action(detail=True, methods=['patch'])
    def complete(self, request, *args, **kwargs):
        """Complete an appointment."""
        instance = self.get_object()
        instance.complete()
        return Response(AppointmentSerializer(instance).data)

    @extend_schema(
        summary='Cancel appointment',
        description='Change appointment status to cancelled.',
        responses={200: AppointmentSerializer}
    )
    @action(detail=True, methods=['patch'])
    def cancel(self, request, *args, **kwargs):
        """Cancel an appointment."""
        instance = self.get_object()
        instance.cancel()
        return Response(AppointmentSerializer(instance).data)

    @extend_schema(
        summary='Mark as no-show',
        description='Mark appointment as no-show.',
        responses={200: AppointmentSerializer}
    )
    @action(detail=True, methods=['patch'])
    def mark_no_show(self, request, *args, **kwargs):
        """Mark an appointment as no-show."""
        instance = self.get_object()
        instance.mark_no_show()
        return Response(AppointmentSerializer(instance).data)

    @extend_schema(
        summary='Get available time slots',
        description='Check available time slots for a given date (helper endpoint).',
        parameters=[
            OpenApiParameter('date', str, OpenApiParameter.QUERY, required=True, description='Date to check (YYYY-MM-DD)'),
            OpenApiParameter('service_id', str, OpenApiParameter.QUERY, required=True, description='Service ID to check availability for'),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request, *args, **kwargs):
        """Get available time slots for a given date."""
        from datetime import datetime, timedelta

        date_str = request.query_params.get('date')
        service_id = request.query_params.get('service_id')

        if not date_str or not service_id:
            return Response(
                {'detail': 'date and service_id parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get service duration
        business = getattr(request, 'business', None)
        if not business:
            return Response(
                {'detail': 'User has no associated business'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = Appointment.objects.filter(business=business).model.objects.get(
                id=service_id, business=business
            )
        except Exception:
            return Response(
                {'detail': 'Service not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get business schedule for the requested date
        from apps.businesses.models import BusinessSchedule
        day_of_week = check_date.weekday()
        schedule = BusinessSchedule.objects.filter(business=business, day_of_week=day_of_week).first()

        available_slots = []
        if not schedule or schedule.is_closed or not schedule.start_time or not schedule.end_time:
            return Response({'available_slots': available_slots})

        duration = service.duration
        
        current_time = datetime.combine(check_date, schedule.start_time)
        end_day_time = datetime.combine(check_date, schedule.end_time)

        while current_time + timedelta(minutes=duration) <= end_day_time:
            slot_start = timezone.make_aware(current_time)
            slot_end = slot_start + timedelta(minutes=duration)

            # Check if this slot overlaps with any existing appointment
            if not Appointment.objects.has_overlap(business, slot_start, slot_end):
                available_slots.append({
                    'start_time': slot_start.isoformat(),
                    'end_time': slot_end.isoformat(),
                })
            
            # Increment slots by 30 minutes (Standard block)
            current_time += timedelta(minutes=30)

        return Response({'available_slots': available_slots})
