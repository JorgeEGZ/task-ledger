"""
Tests for Users app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_verified)

    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_missing_email(self):
        """Test that creating user without email raises error."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='testpass123'
            )

    def test_unique_email(self):
        """Test that email is unique."""
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                password='anotherpass123'
            )

    def test_verify_email(self):
        """Test email verification."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertFalse(user.is_verified)
        user.verify_email()
        self.assertTrue(user.is_verified)


class AuthViewSetTest(APITestCase):
    """Test cases for authentication endpoints."""

    def test_user_registration(self):
        """Test user registration."""
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = {
            'email': 'test@example.com',
            'password': 'pass123',
            'password_confirm': 'different123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_user_login(self):
        """Test user login."""
        # Create user first
        User.objects.create_user(
            email='login@example.com',
            password='loginpass123',
            first_name='Login',
            last_name='User'
        )
        # Login
        data = {
            'email': 'login@example.com',
            'password': 'loginpass123'
        }
        response = self.client.post('/api/v1/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/v1/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test token refresh."""
        user = User.objects.create_user(
            email='refresh@example.com',
            password='refreshpass123'
        )
        refresh = RefreshToken.for_user(user)
        data = {'refresh_token': str(refresh)}
        response = self.client.post('/api/v1/auth/refresh/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_get_current_user(self):
        """Test getting current user info."""
        user = User.objects.create_user(
            email='me@example.com',
            password='mepass123',
            first_name='Me',
            last_name='User'
        )
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'me@example.com')

    def test_unauthenticated_access(self):
        """Test unauthenticated access to protected endpoint."""
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserViewSetTest(APITestCase):
    """Test cases for user profile endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='profilepass123',
            first_name='Profile',
            last_name='User'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(self.refresh.access_token)}')

    def test_get_own_profile(self):
        """Test getting own profile."""
        response = self.client.get(f'/api/v1/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'profile@example.com')

    def test_update_own_profile(self):
        """Test updating own profile."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+1234567890'
        }
        response = self.client.patch(f'/api/v1/users/{self.user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['phone'], '+1234567890')

    def test_list_disabled(self):
        """Test that list endpoint is disabled."""
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
