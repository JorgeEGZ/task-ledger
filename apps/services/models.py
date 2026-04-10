"""
Service model for AgendaCero.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Service(models.Model):
    """
    Service model representing a service offered by a business.

    Each service belongs to a specific business and has a duration and price.
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
        related_name='services',
        help_text="Business this service belongs to"
    )
    name = models.CharField(
        max_length=255,
        help_text="Service name"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Service description"
    )
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Duration in minutes"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Service price"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the service is currently offered"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the service was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the service was last updated"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the service was soft deleted"
    )

    class Meta:
        db_table = 'services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['business', 'name'],
                name='unique_service_name_per_business'
            )
        ]
        indexes = [
            models.Index(fields=['business', 'is_deleted']),
            models.Index(fields=['business', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.duration} min - ${self.price})"

    def soft_delete(self):
        """Mark the service as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restore a soft-deleted service."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def get_appointments_count(self):
        """Return the number of appointments for this service."""
        return self.appointments.filter(is_deleted=False).count()


from django.utils import timezone
