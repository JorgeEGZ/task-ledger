"""
Client model for AgendaCero.
"""

import uuid
from django.db import models
from django.core.validators import EmailValidator


class Client(models.Model):
    """
    Client model representing a customer of a business.

    Each client belongs to a specific business (multi-tenant).
    Supports soft delete for data retention.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID)"
    )
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='clients',
        help_text="Business this client belongs to"
    )
    name = models.CharField(
        max_length=255,
        help_text="Client's full name"
    )
    phone = models.CharField(
        max_length=20,
        help_text="Client's phone number"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        validators=[EmailValidator()],
        help_text="Client's email address"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the client"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the client is active"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the client was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the client was last updated"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the client was soft deleted"
    )

    class Meta:
        db_table = 'clients'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['business', 'email'],
                name='unique_client_email_per_business',
                condition=models.Q(email__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['business', 'is_deleted']),
            models.Index(fields=['business', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def soft_delete(self):
        """Mark the client as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restore a soft-deleted client."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def get_appointments_count(self):
        """Return the number of appointments for this client."""
        return self.appointments.filter(is_deleted=False).count()


from django.utils import timezone
