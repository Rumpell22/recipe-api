"""
Test para los modelos
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models
from core.models import Recipe, Tag, Ingredient


def create_user(email='admin@gmail.com', password='admin.1234'):
    """Crea y regresa un nuevo usuario"""
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):
    """Test de los modelos"""

    def test_create_user_with_email_successful(self):
        """Test si se puede crear un usuario con un email"""
        email = 'test@example.com'
        password = 'holamundo'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Comprueba que el email este normalizado"""
        sample_emails = [
            ['test@EXAMPLE.com', 'test@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['TEST4@example.COM', 'TEST4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email=email)
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Prueba si un usuario con un email vacio devuelve error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test1234')

    def test_create_superuser(self):
        """Prueba que se pueda crear un superusuario"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test1234'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe_success(self):
        """Test para verificar el modelo receta"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test1234'
        )
        recipe = Recipe.objects.create(
            user=user,
            title='Prueba receta',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Prueba de descripcion'
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test para verificar el modelo categoria"""
        user = create_user()
        tag = Tag.objects.create(user=user, name='Tag1')
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test para verificar el modelo ingrediente"""
        user = create_user()
        ingredient = Ingredient.objects.create(user=user, name='Chile')
        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Prueba generando la ruta de la imagen"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
