"""
Tests for Businesses app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Business

User = get_user_model()


class BusinessModelTest(TestCase):
    """Test cases for Business model."""

    def test_create_business(self):
        """Test creating a business."""
        owner = User.objects.create_user(
            email='owner@example.com',
            password='ownerpass123'
        )
        business = Business.objects.create(
            owner=owner,
            name="Test Business"
        )
        self.assertEqual(business.name, "Test Business")
        self.assertEqual(business.owner, owner)
        self.assertTrue(business.is_active)

    def test_business_str(self):
        """Test business string representation."""
        owner = User.objects.create_user(
            email='owner2@example.com',
            password='ownerpass123'
        )
        business = Business.objects.create(
            owner=owner,
            name="My Business"
        )
        self.assertEqual(str(business), "My Business")

    def test_unique_business_name_per_owner(self):
        """Test that business names are unique per owner."""
        owner = User.objects.create_user(
            email='owner3@example.com',
            password='ownerpass123'
        )
        Business.objects.create(owner=owner, name="Same Name")
        with self.assertRaises(Exception):
            Business.objects.create(owner=owner, name="Same Name")

    def test_same_name_different_owners(self):
        """Test that different owners can have same business name."""
        owner1 = User.objects.create_user(email='owner1@example.com', password='pass123')
        owner2 = User.objects.create_user(email='owner2@example.com', password='pass123')
        Business.objects.create(owner=owner1, name="Same Name")
        # This should not raise
        Business.objects.create(owner=owner2, name="Same Name")


class BusinessViewSetTest(APITestCase):
    """Test cases for Business API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='business@example.com',
            password='businesspass123',
            first_name='Business',
            last_name='Owner'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')

    def test_list_businesses(self):
        """Test listing businesses."""
        Business.objects.create(owner=self.user, name="My Business")
        response = self.client.get('/api/v1/businesses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_business(self):
        """Test creating a business."""
        data = {
            'name': 'New Business',
            'phone': '+1234567890',
            'address': '123 Main St',
            'description': 'A test business'
        }
        response = self.client.post('/api/v1/businesses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Business')
        self.assertEqual(response.data['owner'], str(self.user.id))

    def test_retrieve_business(self):
        """Test retrieving a business."""
        business = Business.objects.create(owner=self.user, name="My Business")
        response = self.client.get(f'/api/v1/businesses/{business.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'My Business')

    def test_update_business(self):
        """Test updating a business."""
        business = Business.objects.create(owner=self.user, name="Original Name")
        data = {'name': 'Updated Name'}
        response = self.client.patch(f'/api/v1/businesses/{business.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_delete_business(self):
        """Test deleting a business."""
        business = Business.objects.create(owner=self.user, name="To Delete")
        response = self.client.delete(f'/api/v1/businesses/{business.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Business.objects.count(), 0)

    def test_user_sees_only_own_businesses(self):
        """Test that users only see their own businesses."""
        other_user = User.objects.create_user(email='other@example.com', password='pass123')
        Business.objects.create(owner=other_user, name="Other Business")
        response = self.client.get('/api/v1/businesses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
