"""
Views for User and Authentication endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
)
from common.permissions import IsOwnerOrReadOnly

User = get_user_model()


@extend_schema(tags=['Authentication'])
class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for authentication operations.

    Provides registration, login, token refresh, and user info endpoints.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary='Register a new user',
        description='Create a new user account. A business is automatically created for the user.',
        request=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiExample(
                'Validation Error',
                value={'detail': 'Error message'}
            )
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary='Login user',
        description='Authenticate user and return JWT tokens.',
        request=CustomTokenObtainPairSerializer,
        responses={
            200: OpenApiExample(
                'Login Success',
                value={
                    'access_token': 'eyJ...',
                    'refresh_token': 'eyJ...',
                    'user': {'id': 'uuid', 'email': 'user@example.com'}
                }
            ),
            401: OpenApiExample(
                'Invalid Credentials',
                value={'detail': 'No active account found with the given credentials'}
            )
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login and return JWT tokens."""
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary='Refresh access token',
        description='Get a new access token using a refresh token.',
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiExample(
                'Token Refresh',
                value={'access_token': 'eyJ...'}
            )
        }
    )
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Refresh access token."""
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access_token': str(refresh.access_token)
            })
        except Exception as e:
            return Response(
                {'detail': f'Invalid refresh token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary='Get current user info',
        description='Retrieve the authenticated user\'s profile information.',
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current authenticated user information."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles.

    Users can only view and update their own profiles.
    """

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'put', 'patch']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """Users can only see their own profile."""
        return User.objects.filter(id=self.request.user.id)

    @extend_schema(
        summary='Get user profile',
        description='Retrieve a user\'s profile. Users can only view their own profile.',
        responses={200: UserSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Ensure users can only view their own profile
        if instance.id != request.user.id:
            return Response(
                {'detail': 'You can only view your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary='Update user profile',
        description='Update the authenticated user\'s profile information.',
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Ensure users can only update their own profile
        if instance.id != request.user.id:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        """List endpoint disabled for security."""
        return Response(
            {'detail': 'List endpoint is disabled for security reasons'},
            status=status.HTTP_403_FORBIDDEN
        )
