"""
Views for Business endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from common.permissions import IsBusinessOwner
from common.pagination import StandardPagination
from .models import Business
from .serializers import BusinessSerializer, BusinessListSerializer, BusinessUpdateSerializer


@extend_schema(tags=['Businesses'])
class BusinessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing businesses.

    Users can only access businesses they own.
    """

    queryset = Business.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    pagination_class = StandardPagination
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'list':
            return BusinessListSerializer
        elif self.action in ['update', 'partial_update']:
            return BusinessUpdateSerializer
        return BusinessSerializer

    def get_queryset(self):
        """
        Filter businesses to only those owned by the current user.
        """
        return Business.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        Set the owner to the current user when creating a business.
        """
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary='List businesses',
        description='Retrieve all businesses owned by the authenticated user.',
        responses={200: BusinessListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Create business',
        description='Create a new business. The authenticated user becomes the owner.',
        request=BusinessSerializer,
        responses={
            201: BusinessSerializer,
            400: OpenApiExample('Validation Error', value={'detail': 'Error message'})
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Get business details',
        description='Retrieve details of a specific business owned by the user.',
        responses={200: BusinessSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update business',
        description='Update a business owned by the authenticated user.',
        request=BusinessUpdateSerializer,
        responses={200: BusinessSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Delete business',
        description='Delete a business owned by the authenticated user.',
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
