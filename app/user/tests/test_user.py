"""Test para la api de usuarios"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Crea y retorna un nuevo usuario"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Prueba las features que no requieran permisos"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creacion de usuario sea exitosa"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertEqual(user.email, payload['email'])

    def test_user_with_email_exists_error(self):
        """Test para cuando el email exista"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_shor_error(self):
        """Test para cuando la contrasena sea muy pequena"""
        payload = {
            'email': 'test@example.com',
            'password': 'test',
            'name': 'Test',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generar token para usuarios validos"""
        user_details = {
            'email': 'test@example.com',
            'password': 'test',
            'name': 'Test',
        }
        create_user(**user_details)
        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentiales(self):
        """Test no genera token usuario invalido"""
        user_details = {
            'email': 'test@example.com',
            'password': 'test',
            'name': 'Test',
        }
        create_user(**user_details)
        payload = {
            'email': 'test@example.com',
            'password': 'testING',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_empty_password(self):
        """Test no genera token cuando no existe password"""
        user_details = {
            'email': 'test@example.com',
            'password': 'test',
            'name': 'Test',
        }
        create_user(**user_details)
        payload = {
            'email': 'test@example.com',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrive_user_aunothorized(self):
        """Test para probar auth del usuario"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test que requieren autenticacion"""

    def setUp(self):
        self.user = create_user(
            email='admin@example.com',
            password='admin',
            name='admin',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile(self):
        """Test para obtener el perfil del usuario"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
        })

    def test_post_me_not_allow(self):
        """Prueba que post no sea aceptado por el endpoint"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_profile(self):
        """Test de actualizar usuario"""
        payload = {
            'name': 'admin',
            'password': 'adminholamundo'
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
