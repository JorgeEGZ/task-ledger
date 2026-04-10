"""
Views for Client endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from common.permissions import IsBusinessOwner
from common.pagination import StandardPagination
from .models import Client
from .serializers import ClientSerializer, ClientCreateSerializer, ClientUpdateSerializer


@extend_schema(tags=['Clients'])
class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clients.

    Clients are scoped to the authenticated user's business.
    Supports filtering, searching, and ordering.
    """

    queryset = Client.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['business', 'is_active']
    search_fields = ['name', 'phone', 'email']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClientUpdateSerializer
        return ClientSerializer

    def get_queryset(self):
        """
        Filter clients to only those belonging to the current user's business.
        """
        user = self.request.user
        business = getattr(user, 'businesses', None)
        if business and business.exists():
            self.request.business = business.first()
            return Client.objects.filter(
                business=business.first(),
                is_deleted=False
            )
        return Client.objects.none()

    def perform_create(self, serializer):
        """
        Set the business to the current user's business when creating a client.
        """
        business = getattr(self.request, 'business', None)
        if not business:
            raise serializers.ValidationError({'business': 'User has no associated business.'})
        serializer.save(business=business)

    @extend_schema(
        summary='List clients',
        description='Retrieve all clients for the authenticated user\'s business.',
        parameters=[
            OpenApiParameter('search', str, OpenApiParameter.QUERY, description='Search by name, phone, or email'),
            OpenApiParameter('is_active', bool, OpenApiParameter.QUERY, description='Filter by active status'),
            OpenApiParameter('ordering', str, OpenApiParameter.QUERY, description='Order by field (name, created_at, etc.)'),
        ],
        responses={200: ClientSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Create client',
        description='Create a new client for the authenticated user\'s business.',
        request=ClientCreateSerializer,
        responses={
            201: ClientSerializer,
            400: OpenApiExample('Validation Error', value={'detail': 'Error message'})
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Get client details',
        description='Retrieve details of a specific client.',
        responses={200: ClientSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update client',
        description='Update a client\'s information.',
        request=ClientUpdateSerializer,
        responses={200: ClientSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Delete client',
        description='Soft delete a client (marks as deleted without removing from database).',
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
