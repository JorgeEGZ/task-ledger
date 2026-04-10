"""
Custom permissions for multi-tenant data access control.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return hasattr(obj, 'owner') and obj.owner == request.user


class IsBusinessOwner(permissions.BasePermission):
    """
    Custom permission to ensure users can only access their own business data.

    This is the core multi-tenant permission that ensures data isolation.
    """

    def has_permission(self, request, view):
        # Safe methods still require authentication
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Ensure the object belongs to the user's business
        if hasattr(obj, 'business'):
            return obj.business.owner == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsBusinessOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read access to authenticated users,
    but write access only to business owners.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'business'):
            return obj.business.owner == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read access to authenticated users,
    but write access only to admin users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission to only allow verified users to access certain endpoints.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_verified', False)
        )
