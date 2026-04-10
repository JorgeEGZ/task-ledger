"""
Appointment model for AgendaCero.
"""

import uuid
from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class AppointmentStatus(models.TextChoices):
    """Appointment status choices."""
    SCHEDULED = 'scheduled', 'Scheduled'
    CONFIRMED = 'confirmed', 'Confirmed'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'


class AppointmentManager(models.Manager):
    """Custom manager for Appointment model with overlap detection."""

    def get_overlapping(self, business, start_time, end_time, exclude_id=None):
        """
        Find all appointments that overlap with the given time range.

        Args:
            business: The business to check for overlaps
            start_time: Start of the time range
            end_time: End of the time range
            exclude_id: Optional appointment ID to exclude (for updates)

        Returns:
            QuerySet of overlapping appointments
        """
        queryset = self.get_queryset().filter(
            business=business,
            is_deleted=False,
            status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
        )

        # Exclude a specific appointment (useful for updates)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        # Check for overlaps:
        # Two time ranges overlap if: start1 < end2 AND end1 > start2
        return queryset.filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        )

    def has_overlap(self, business, start_time, end_time, exclude_id=None):
        """
        Check if there's any overlap for the given time range.

        Returns:
            True if overlap exists, False otherwise
        """
        return self.get_overlapping(business, start_time, end_time, exclude_id).exists()


class Appointment(models.Model):
    """
    Appointment model for scheduling client appointments.

    Includes overlap prevention to ensure no double-booking
    for the same business.
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
        related_name='appointments',
        help_text="Business this appointment belongs to"
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text="Client for this appointment"
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text="Service being provided"
    )
    start_time = models.DateTimeField(
        help_text="Appointment start time"
    )
    end_time = models.DateTimeField(
        help_text="Appointment end time"
    )
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
        help_text="Current appointment status"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes for the appointment"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the appointment was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the appointment was last updated"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the appointment was soft deleted"
    )

    objects = AppointmentManager()

    class Meta:
        db_table = 'appointments'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='end_time_after_start_time'
            )
        ]
        indexes = [
            models.Index(fields=['business', 'start_time']),
            models.Index(fields=['business', 'status', 'is_deleted']),
            models.Index(fields=['client', 'start_time']),
        ]

    def __str__(self):
        return f"{self.client.name} - {self.service.name} ({self.start_time})"

    def clean(self):
        """Validate appointment data."""
        super().clean()

        # Validate end_time is after start_time
        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                raise ValidationError({'end_time': 'End time must be after start time.'})

        # Check for overlapping appointments
        if self.business and self.start_time and self.end_time:
            if Appointment.objects.has_overlap(
                self.business,
                self.start_time,
                self.end_time,
                exclude_id=self.id
            ):
                raise ValidationError(
                    {'start_time': 'This time slot conflicts with an existing appointment.'}
                )

    def save(self, *args, **kwargs):
        """Override save to run validation and auto-calculate end_time if needed."""
        # Auto-calculate end_time from service duration if not provided
        if self.service and not self.end_time:
            self.end_time = self.start_time + timedelta(minutes=self.service.duration)

        # Run validation
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Mark the appointment as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restore a soft-deleted appointment."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def confirm(self):
        """Change appointment status to confirmed."""
        self.status = AppointmentStatus.CONFIRMED
        self.save(update_fields=['status', 'updated_at'])

    def complete(self):
        """Change appointment status to completed."""
        self.status = AppointmentStatus.COMPLETED
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self):
        """Change appointment status to cancelled."""
        self.status = AppointmentStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])

    def mark_no_show(self):
        """Mark appointment as no-show."""
        self.status = AppointmentStatus.NO_SHOW
        self.save(update_fields=['status', 'updated_at'])

    @property
    def duration_minutes(self):
        """Return appointment duration in minutes."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0

    @property
    def is_upcoming(self):
        """Check if appointment is in the future."""
        return self.start_time > timezone.now()

    @property
    def is_past(self):
        """Check if appointment is in the past."""
        return self.start_time < timezone.now()
