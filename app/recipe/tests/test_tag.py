"""
Test para las categorias
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_user(email='admin@gmail.com', password='admin.1234'):
    """Crea y regresa el usuario"""
    return get_user_model().objects.create_user(email=email, password=password)

def create_tag(user,name='helados'):
    return Tag.objects.create(user=user,name=name)


def detail_url_tag(id_tag):
    """Crea y regresa el link de la categoria"""
    return reverse('recipe:tag-detail', args=[id_tag])


class TestTagPublicAPI(TestCase):
    """Prueba la parte publica de la api"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Autenticacion requerida para ver las categorias"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestTagPrivateAPI(TestCase):
    """Prueba la parte privada de la api"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test para obtener las categorias"""
        Tag.objects.create(name='carne', user=self.user)
        Tag.objects.create(name='vegan', user=self.user)
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tag_limited_to_user(self):
        """Prueba que las categorias le pertenezcan al usuario"""
        user2 = create_user(email='adsds@gmail.com')
        Tag.objects.create(user=user2, name='manzanilla')
        tag = Tag.objects.create(user=self.user, name='pizza')
        res = self.client.get(TAGS_URL)

        tag_selected = Tag.objects.get(id=tag.id)
        serializer = TagSerializer(tag_selected)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.user, self.user)
        self.assertEqual((len(res.data)), 1)
        self.assertEqual(res.data[0], serializer.data)

    def test_update_tag(self):
        """Prueba actualizar la categoria"""
        tag = Tag.objects.create(user=self.user, name='prueba')
        payload = {'name': 'pastel'}
        url_tag = detail_url_tag(tag.id)

        res = self.client.put(url_tag, payload)
        tag.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Prueba eliminar la categoria"""
        tag = create_tag(self.user)
        url = detail_url_tag(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_delete_tag_unowned(self):
        """Prueba eliminar la categoria de alguien mas"""
        new_user  = create_user(email='test@test.com')
        tag = create_tag(new_user)
        url = detail_url_tag(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_404_NOT_FOUND)
        self.assertTrue(Tag.objects.filter(id=tag.id).exists())