"""
Tests for Appointments app.
"""

from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.businesses.models import Business
from apps.clients.models import Client
from apps.services.models import Service
from .models import Appointment, AppointmentStatus

User = get_user_model()


class AppointmentModelTest(TestCase):
    """Test cases for Appointment model."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='ownerpass123'
        )
        self.business = Business.objects.create(owner=self.owner, name="Test Business")
        self.client = Client.objects.create(
            business=self.business,
            name="Test Client",
            phone="+1234567890"
        )
        self.service = Service.objects.create(
            business=self.business,
            name="Test Service",
            duration=30,
            price=25.00
        )

    def test_create_appointment(self):
        """Test creating an appointment."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        self.assertEqual(appointment.status, AppointmentStatus.SCHEDULED)
        self.assertEqual(appointment.business, self.business)
        self.assertEqual(appointment.client, self.client)

    def test_appointment_str(self):
        """Test appointment string representation."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        self.assertIn("Test Client", str(appointment))
        self.assertIn("Test Service", str(appointment))

    def test_end_time_must_be_after_start_time(self):
        """Test that end time must be after start time."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time - timedelta(minutes=30)  # Before start
        with self.assertRaises(Exception):
            Appointment.objects.create(
                business=self.business,
                client=self.client,
                service=self.service,
                start_time=start_time,
                end_time=end_time
            )

    def test_overlapping_appointments_prevented(self):
        """Test that overlapping appointments are prevented."""
        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(minutes=30)

        # Create first appointment
        Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )

        # Try to create overlapping appointment
        overlap_start = start_time + timedelta(minutes=15)
        overlap_end = overlap_start + timedelta(minutes=30)
        with self.assertRaises(Exception):
            Appointment.objects.create(
                business=self.business,
                client=self.client,
                service=self.service,
                start_time=overlap_start,
                end_time=overlap_end
            )

    def test_non_overlapping_appointments_allowed(self):
        """Test that non-overlapping appointments are allowed."""
        start_time = timezone.now() + timedelta(days=1, hours=10)
        end_time = start_time + timedelta(minutes=30)

        # Create first appointment
        Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )

        # Create non-overlapping appointment (after the first one)
        second_start = end_time  # Starts right after first ends
        second_end = second_start + timedelta(minutes=30)
        second_appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=second_start,
            end_time=second_end
        )
        self.assertIsNotNone(second_appointment.id)

    def test_soft_delete(self):
        """Test soft delete functionality."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        self.assertFalse(appointment.is_deleted)
        appointment.soft_delete()
        self.assertTrue(appointment.is_deleted)

    def test_status_transitions(self):
        """Test appointment status transitions."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )

        # Confirm
        appointment.confirm()
        self.assertEqual(appointment.status, AppointmentStatus.CONFIRMED)

        # Complete
        appointment.complete()
        self.assertEqual(appointment.status, AppointmentStatus.COMPLETED)

    def test_cancel_appointment(self):
        """Test cancelling an appointment."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        appointment.cancel()
        self.assertEqual(appointment.status, AppointmentStatus.CANCELLED)

    def test_mark_no_show(self):
        """Test marking appointment as no-show."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        appointment.mark_no_show()
        self.assertEqual(appointment.status, AppointmentStatus.NO_SHOW)

    def test_duration_minutes_property(self):
        """Test duration_minutes property."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=45)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        self.assertEqual(appointment.duration_minutes, 45)


class AppointmentViewSetTest(APITestCase):
    """Test cases for Appointment API endpoints."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='apptowner@example.com',
            password='ownerpass123'
        )
        self.business = Business.objects.create(owner=self.owner, name="Test Business")
        self.client = Client.objects.create(
            business=self.business,
            name="Test Client",
            phone="+1234567890"
        )
        self.service = Service.objects.create(
            business=self.business,
            name="Test Service",
            duration=30,
            price=25.00
        )
        self.refresh = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')

    def test_list_appointments(self):
        """Test listing appointments."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        response = self.client.get('/api/v1/appointments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_appointment(self):
        """Test creating an appointment."""
        start_time = timezone.now() + timedelta(days=2)
        data = {
            'client': str(self.client.id),
            'service': str(self.service.id),
            'start_time': start_time.isoformat(),
            'notes': 'Test appointment'
        }
        response = self.client.post('/api/v1/appointments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['notes'], 'Test appointment')

    def test_create_overlapping_appointment_fails(self):
        """Test that creating overlapping appointment fails."""
        start_time = timezone.now() + timedelta(days=3, hours=10)
        end_time = start_time + timedelta(minutes=30)

        # Create first appointment
        Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )

        # Try to create overlapping appointment
        overlap_start = start_time + timedelta(minutes=15)
        data = {
            'client': str(self.client.id),
            'service': str(self.service.id),
            'start_time': overlap_start.isoformat()
        }
        response = self.client.post('/api/v1/appointments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_time', response.data)

    def test_retrieve_appointment(self):
        """Test retrieving an appointment."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        response = self.client.get(f'/api/v1/appointments/{appointment.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['client_details']['name'], 'Test Client')

    def test_update_appointment(self):
        """Test updating an appointment."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        data = {'notes': 'Updated notes'}
        response = self.client.patch(f'/api/v1/appointments/{appointment.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notes'], 'Updated notes')

    def test_delete_appointment_soft(self):
        """Test soft deleting an appointment."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        response = self.client.delete(f'/api/v1/appointments/{appointment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        appointment.refresh_from_db()
        self.assertTrue(appointment.is_deleted)

    def test_update_status(self):
        """Test updating appointment status."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        data = {'status': 'confirmed'}
        response = self.client.patch(
            f'/api/v1/appointments/{appointment.id}/status/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')

    def test_confirm_action(self):
        """Test confirm action endpoint."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        response = self.client.patch(f'/api/v1/appointments/{appointment.id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')

    def test_cancel_action(self):
        """Test cancel action endpoint."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        appointment = Appointment.objects.create(
            business=self.business,
            client=self.client,
            service=self.service,
            start_time=start_time,
            end_time=end_time
        )
        response = self.client.patch(f'/api/v1/appointments/{appointment.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')
