"""
Views for Service endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from common.permissions import IsBusinessOwner
from common.pagination import StandardPagination
from .models import Service
from .serializers import ServiceSerializer, ServiceCreateSerializer, ServiceUpdateSerializer


@extend_schema(tags=['Services'])
class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing services.

    Services are scoped to the authenticated user's business.
    Supports filtering, searching, and ordering.
    """

    queryset = Service.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['business', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'duration', 'created_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ServiceUpdateSerializer
        return ServiceSerializer

    def get_queryset(self):
        """
        Filter services to only those belonging to the current user's business.
        """
        user = self.request.user
        business = getattr(user, 'businesses', None)
        if business and business.exists():
            self.request.business = business.first()
            return Service.objects.filter(
                business=business.first(),
                is_deleted=False
            )
        return Service.objects.none()

    def perform_create(self, serializer):
        """
        Set the business to the current user's business when creating a service.
        """
        business = getattr(self.request, 'business', None)
        if not business:
            raise serializers.ValidationError({'business': 'User has no associated business.'})
        serializer.save(business=business)

    @extend_schema(
        summary='List services',
        description='Retrieve all services for the authenticated user\'s business.',
        parameters=[
            OpenApiParameter('search', str, OpenApiParameter.QUERY, description='Search by name or description'),
            OpenApiParameter('is_active', bool, OpenApiParameter.QUERY, description='Filter by active status'),
            OpenApiParameter('ordering', str, OpenApiParameter.QUERY, description='Order by field (name, price, duration, etc.)'),
        ],
        responses={200: ServiceSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Create service',
        description='Create a new service for the authenticated user\'s business.',
        request=ServiceCreateSerializer,
        responses={
            201: ServiceSerializer,
            400: OpenApiExample('Validation Error', value={'detail': 'Error message'})
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Get service details',
        description='Retrieve details of a specific service.',
        responses={200: ServiceSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update service',
        description='Update a service\'s information.',
        request=ServiceUpdateSerializer,
        responses={200: ServiceSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Delete service',
        description='Soft delete a service (marks as deleted without removing from database).',
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
