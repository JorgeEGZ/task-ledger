"""
Business model for AgendaCero.
"""

import uuid
from django.db import models
from django.conf import settings


class Business(models.Model):
    """
    Business model representing a tenant in the multi-tenant system.

    Each business is owned by a single user and contains all the
    business-specific data (clients, services, appointments).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID)"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='businesses',
        help_text="User who owns this business"
    )
    name = models.CharField(
        max_length=255,
        help_text="Business name"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Business phone number"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Business physical address"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Business description"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the business is active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the business was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the business was last updated"
    )

    class Meta:
        db_table = 'businesses'
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_business_name_per_owner'
            )
        ]

    def __str__(self):
        return self.name

    def get_clients_count(self):
        """Return the number of clients for this business."""
        return self.clients.filter(is_deleted=False).count()

    def get_services_count(self):
        """Return the number of services for this business."""
        return self.services.filter(is_deleted=False).count()

    def get_appointments_count(self):
        """Return the number of appointments for this business."""
        return self.appointments.filter(is_deleted=False).count()

class BusinessSchedule(models.Model):
    """
    Business Operating Hours.
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day_of_week = models.IntegerField(
        choices=[
            (0, 'Monday'),
            (1, 'Tuesday'),
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ]
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        db_table = 'business_schedules'
        unique_together = ('business', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.business.name} - Day {self.day_of_week}"
