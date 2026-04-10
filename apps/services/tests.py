"""
Tests for Services app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.businesses.models import Business
from .models import Service

User = get_user_model()


class ServiceModelTest(TestCase):
    """Test cases for Service model."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='ownerpass123'
        )
        self.business = Business.objects.create(owner=self.owner, name="Test Business")

    def test_create_service(self):
        """Test creating a service."""
        service = Service.objects.create(
            business=self.business,
            name="Haircut",
            duration=30,
            price=25.00
        )
        self.assertEqual(service.name, "Haircut")
        self.assertEqual(service.duration, 30)
        self.assertEqual(service.price, 25.00)
        self.assertEqual(service.business, self.business)

    def test_service_str(self):
        """Test service string representation."""
        service = Service.objects.create(
            business=self.business,
            name="Beard Trim",
            duration=15,
            price=10.00
        )
        self.assertEqual(str(service), "Beard Trim (15 min - $10.00)")

    def test_minimum_duration(self):
        """Test that duration must be positive."""
        with self.assertRaises(Exception):
            Service.objects.create(
                business=self.business,
                name="Invalid Service",
                duration=0,
                price=10.00
            )

    def test_minimum_price(self):
        """Test that price cannot be negative."""
        with self.assertRaises(Exception):
            Service.objects.create(
                business=self.business,
                name="Free Service",
                duration=30,
                price=-5.00
            )

    def test_zero_price_allowed(self):
        """Test that zero price is allowed."""
        service = Service.objects.create(
            business=self.business,
            name="Free Consultation",
            duration=15,
            price=0.00
        )
        self.assertEqual(service.price, 0.00)

    def test_unique_name_per_business(self):
        """Test that service names are unique per business."""
        Service.objects.create(
            business=self.business,
            name="Duplicate Name",
            duration=30,
            price=25.00
        )
        with self.assertRaises(Exception):
            Service.objects.create(
                business=self.business,
                name="Duplicate Name",
                duration=45,
                price=30.00
            )

    def test_soft_delete(self):
        """Test soft delete functionality."""
        service = Service.objects.create(
            business=self.business,
            name="To Delete",
            duration=30,
            price=25.00
        )
        self.assertFalse(service.is_deleted)
        service.soft_delete()
        self.assertTrue(service.is_deleted)


class ServiceViewSetTest(APITestCase):
    """Test cases for Service API endpoints."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='serviceowner@example.com',
            password='ownerpass123'
        )
        self.business = Business.objects.create(owner=self.owner, name="Test Business")
        self.refresh = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')

    def test_list_services(self):
        """Test listing services."""
        Service.objects.create(
            business=self.business,
            name="Service One",
            duration=30,
            price=25.00
        )
        response = self.client.get('/api/v1/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_service(self):
        """Test creating a service."""
        data = {
            'name': 'New Service',
            'description': 'A test service',
            'duration': 45,
            'price': 35.00
        }
        response = self.client.post('/api/v1/services/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Service')
        self.assertEqual(response.data['duration'], 45)

    def test_retrieve_service(self):
        """Test retrieving a service."""
        service = Service.objects.create(
            business=self.business,
            name="Retrieve Service",
            duration=30,
            price=25.00
        )
        response = self.client.get(f'/api/v1/services/{service.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Service')

    def test_update_service(self):
        """Test updating a service."""
        service = Service.objects.create(
            business=self.business,
            name="Original Name",
            duration=30,
            price=25.00
        )
        data = {'name': 'Updated Name', 'price': 30.00}
        response = self.client.patch(f'/api/v1/services/{service.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')
        self.assertEqual(response.data['price'], '30.00')

    def test_delete_service_soft(self):
        """Test soft deleting a service."""
        service = Service.objects.create(
            business=self.business,
            name="To Delete",
            duration=30,
            price=25.00
        )
        response = self.client.delete(f'/api/v1/services/{service.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        service.refresh_from_db()
        self.assertTrue(service.is_deleted)

    def test_search_services(self):
        """Test searching services."""
        Service.objects.create(
            business=self.business,
            name="Searchable Service",
            duration=30,
            price=25.00
        )
        response = self.client.get('/api/v1/services/?search=Searchable')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_order_by_price(self):
        """Test ordering services by price."""
        Service.objects.create(business=self.business, name="Cheap", duration=15, price=10.00)
        Service.objects.create(business=self.business, name="Expensive", duration=60, price=100.00)
        response = self.client.get('/api/v1/services/?ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['name'], 'Cheap')
