"""
Custom User model for AgendaCero.
"""

import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('Email address is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model extending AbstractUser.

    Uses email as the primary identifier instead of username.
    Supports email verification and phone number storage.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID)"
    )
    email = models.EmailField(
        unique=True,
        help_text="User's email address (used for authentication)"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="User's phone number"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the user was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the user was last updated"
    )

    # Remove username field from being required
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Ensure email is always stored in lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def verify_email(self):
        """Mark the user's email as verified."""
        self.is_verified = True
        self.save(update_fields=['is_verified'])

    @property
    def business(self):
        """Return the first business owned by this user (useful for single-tenant-per-user setups)."""
        return self.businesses.first()
