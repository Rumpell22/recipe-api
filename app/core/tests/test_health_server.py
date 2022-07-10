"""
Tests para chckear la salud del servidor
"""

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthServerTests(SimpleTestCase):
    """Test para probar si el server funciona"""

    def test_check_health_server(self):
        """Test para la salud del server"""
        client = APIClient()
        url = reverse('check-health')
        res = client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
