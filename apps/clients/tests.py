"""
Tests for Clients app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.businesses.models import Business
from .models import Client

User = get_user_model()


class ClientModelTest(TestCase):
    """Test cases for Client model."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='ownerpass123'
        )
        self.business = Business.objects.create(owner=self.owner, name="Test Business")

    def test_create_client(self):
        """Test creating a client."""
        client = Client.objects.create(
            business=self.business,
            name="John Doe",
            phone="+1234567890",
            email="john@example.com"
        )
        self.assertEqual(client.name, "John Doe")
        self.assertEqual(client.business, self.business)
        self.assertTrue(client.is_active)
        self.assertFalse(client.is_deleted)

    def test_client_str(self):
        """Test client string representation."""
        client = Client.objects.create(
            business=self.business,
            name="Jane Doe",
            phone="+1234567890"
        )
        self.assertEqual(str(client), "Jane Doe")

    def test_soft_delete(self):
        """Test soft delete functionality."""
        client = Client.objects.create(
            business=self.business,
            name="To Delete",
            phone="+1234567890"
        )
        self.assertFalse(client.is_deleted)
        client.soft_delete()
        self.assertTrue(client.is_deleted)
        self.assertIsNotNone(client.deleted_at)

    def test_restore(self):
        """Test restoring a soft-deleted client."""
        client = Client.objects.create(
            business=self.business,
            name="To Restore",
            phone="+1234567890"
        )
        client.soft_delete()
        client.restore()
        self.assertFalse(client.is_deleted)
        self.assertIsNone(client.deleted_at)

    def test_unique_email_per_business(self):
        """Test that email is unique within a business."""
        Client.objects.create(
            business=self.business,
            name="First Client",
            phone="+1234567890",
            email="duplicate@example.com"
        )
        with self.assertRaises(Exception):
            Client.objects.create(
                business=self.business,
                name="Second Client",
                phone="+0987654321",
                email="duplicate@example.com"
            )

    def test_same_email_different_business(self):
        """Test that same email can exist in different businesses."""
        other_business = Business.objects.create(
            owner=self.owner,
            name="Other Business"
        )
        Client.objects.create(
            business=self.business,
            name="Client 1",
            email="same@example.com",
            phone="+1234567890"
        )
        # This should not raise
        Client.objects.create(
            business=other_business,
            name="Client 2",
            email="same@example.com",
            phone="+1234567890"
        )


class ClientViewSetTest(APITestCase):
    """Test cases for Client API endpoints."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='clientowner@example.com',
            password='ownerpass123'
        )
        self.business = Business.objects.create(owner=self.owner, name="Test Business")
        self.refresh = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')

    def test_list_clients(self):
        """Test listing clients."""
        Client.objects.create(
            business=self.business,
            name="Client One",
            phone="+1234567890"
        )
        response = self.client.get('/api/v1/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_client(self):
        """Test creating a client."""
        data = {
            'name': 'New Client',
            'phone': '+1234567890',
            'email': 'newclient@example.com',
            'notes': 'Test notes'
        }
        response = self.client.post('/api/v1/clients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Client')

    def test_retrieve_client(self):
        """Test retrieving a client."""
        client = Client.objects.create(
            business=self.business,
            name="Retrieve Me",
            phone="+1234567890"
        )
        response = self.client.get(f'/api/v1/clients/{client.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Me')

    def test_update_client(self):
        """Test updating a client."""
        client = Client.objects.create(
            business=self.business,
            name="Original Name",
            phone="+1234567890"
        )
        data = {'name': 'Updated Name'}
        response = self.client.patch(f'/api/v1/clients/{client.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_delete_client_soft(self):
        """Test soft deleting a client."""
        client = Client.objects.create(
            business=self.business,
            name="To Delete",
            phone="+1234567890"
        )
        response = self.client.delete(f'/api/v1/clients/{client.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Client should still exist but be marked as deleted
        client.refresh_from_db()
        self.assertTrue(client.is_deleted)

    def test_search_clients(self):
        """Test searching clients."""
        Client.objects.create(
            business=self.business,
            name="Searchable Client",
            phone="+1234567890",
            email="search@example.com"
        )
        response = self.client.get('/api/v1/clients/?search=Searchable')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_active(self):
        """Test filtering clients by active status."""
        Client.objects.create(business=self.business, name="Active Client", phone="+1234567890", is_active=True)
        Client.objects.create(business=self.business, name="Inactive Client", phone="+0987654321", is_active=False)
        response = self.client.get('/api/v1/clients/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
