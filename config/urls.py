"""
URL configuration for AgendaCero project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter

# Import viewsets
from apps.users.views import UserViewSet, AuthViewSet
from apps.businesses.views import BusinessViewSet
from apps.clients.views import ClientViewSet
from apps.services.views import ServiceViewSet
from apps.appointments.views import AppointmentViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

# Authentication endpoints (not using router for custom actions)
auth_patterns = [
    path('register/', AuthViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('refresh/', AuthViewSet.as_view({'post': 'refresh'}), name='auth-refresh'),
    path('me/', AuthViewSet.as_view({'get': 'me'}), name='auth-me'),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API versioning
    path('api/v1/', include([
        # Authentication
        path('auth/', include(auth_patterns)),
        # Main router
        path('', include(router.urls)),
    ])),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health check
    path('api/health/', lambda request: JsonResponse({'status': 'healthy', 'version': '1.0.0'}), name='health'),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
