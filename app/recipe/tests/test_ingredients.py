"""
Test para los ingredientes
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

URL_INGREDIENT = reverse('recipe:ingredient-list')


def create_user(email='admin@gmail.com', password='admin.1234'):
    """Crea y retorna el usuario"""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


def create_ingredient(name, user):
    return Ingredient.objects.create(name=name, user=user)


def detail_url(id_ingredient):
    """Regresa la url del retrieve"""
    return reverse('recipe:ingredient-detail', args={id_ingredient})


class PublicIngredientAPITests(TestCase):
    """Prueba la parte sin auth de la api"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Login requerido para obtener recetas"""
        res = self.client.get(URL_INGREDIENT)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    """Test para la parte privada de la api"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_recipe_ingredients(self):
        """Prueba obtener los ingredientes"""
        create_ingredient('carne', self.user)
        create_ingredient('mayonesa', self.user)

        res = self.client.get(URL_INGREDIENT)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(serializer.data, res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_ingredients_limited_by_user(self):
        """Obtiene los ingredientes del usuario"""
        new_user = create_user(email='xd@gmail.com')

        create_ingredient('ketchup', new_user)
        ingredient = create_ingredient('salsa', self.user)

        res = self.client.get(URL_INGREDIENT)
        serializer = IngredientSerializer(ingredient)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.user, self.user)
        self.assertEqual(res.data[0], serializer.data)
        self.assertEqual(len(res.data), 1)

    def test_ingredient_update(self):
        """Prueba actualizar un ingrediente"""
        ingredient = create_ingredient('sal', self.user)
        payload = {
            'name': 'salsa soya'
        }
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_own_ingredient(self):
        """Prueba borrar ingrediente propio """
        ingredient = create_ingredient('sal', self.user)
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertTrue(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_delete_unowned_ingredient(self):
        """Prueba eliminar ingrediente ajeno"""
        ingredient = create_ingredient('sal', self.user)
        url = detail_url(ingredient)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        """Prueba filtar los ingredientes asignados a la receta"""
        ingredient_1 = create_ingredient('sal', self.user)
        ingredient_2 = create_ingredient('azucar',self.user)
        recipe = Recipe.objects.create(
            title='Pastel',
            time_minutes=5,
            price=Decimal('10.10'),
            user=self.user
        )
        recipe.ingredientes.add(ingredient_1)
        res = self.client.get(URL_INGREDIENT,{'assigned_only': 1})

        serializer_1 = IngredientSerializer(ingredient_1)
        serializer_2 = IngredientSerializer(ingredient_2)
        self.assertIn(serializer_1.data,res.data)
        self.assertNotIn(serializer_2.data,res.data)

    def test_filter_ingredients_unique(self):
        """Prueba filter unique list"""
        ingredient = create_ingredient('sal', self.user)
        Ingredient.objects.create(user=self.user,name='Lentejas')
        recipe_1 = Recipe.objects.create(
            title='Huevos con salsa',
            time_minutes=50,
            price=Decimal('7.00'),
            user=self.user
        )
        recipe_2 = Recipe.objects.create(
            title='Huevos fritos',
            time_minutes=20,
            price=Decimal('4.00'),
            user=self.user
        )
        recipe_1.ingredientes.add(ingredient)
        recipe_2.ingredientes.add(ingredient)

        res = self.client.get(URL_INGREDIENT,{'assigned_only': 1 })
        self.assertEqual(len(res.data),1)