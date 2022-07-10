"""
Tests para las recetas
"""
import os
import tempfile
import uuid
from decimal import Decimal

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Regresa la url del retrieve de la receta"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Crea y regresa una receta de ej"""
    default = {
        'title': uuid.uuid4().hex.upper()[0:6],
        'time_minutes': 50,
        'price': Decimal('5.5'),
        'link': 'https://prueba.com/test',
        'description': 'hola mundo'
    }
    default.update(**params)
    recipe = Recipe.objects.create(user=user, **default)
    return recipe


def image_upload_url(recipe_id):
    """Regresa la url para subir imagen"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_ingredient(name, user):
    return Ingredient.objects.create(name=name, user=user)


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test para la parte publica """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Prueba los permisos para ver las recetas"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test privados para la parte privada"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='admin@gmail.com', password='admin.1234')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test obtener las recetas"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(3, recipes.count())
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_recipe_limited_to_user(self):
        """Test para las recetas del usuario"""
        other_user = create_user(email='test@gmail.com', password='admin.1234')
        create_recipe(other_user)
        create_recipe(self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail(self):
        """Test para obtener la receta"""
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        """Test para crear la receta"""
        payload = {
            'title': uuid.uuid4().hex.upper()[0:6],
            'time_minutes': 50,
            'price': Decimal('5.5'),
            'link': 'https://prueba.com/test',
            'description': 'hola mundo'
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Actualizacion parcial"""
        original_link = 'https://brazzers.com'
        recipe = create_recipe(
            user=self.user,
            title='prueba',
            link=original_link
        )
        payload = {'title': 'holamundo'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Actualizacion completa"""
        recipe = create_recipe(
            user=self.user,
            title='prueba',
            link='https://brazzers.com',
            description='holamundo'
        )
        payload = {
            'title': 'holamundo',
            'link': 'https://elamigos.com',
            'description': 'hola mundo',
            'time_minutes': 10,
            'price': Decimal('5.5'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        """Prueba que actualizar el usuario de error"""
        new_user = create_user(email='user2@example.com', password='admin')
        recipe = create_recipe(user=self.user)
        payload = {
            'user': new_user.id
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Borra la receta"""
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_delete_other_user_error(self):
        """Borrar la receta de otra persona da error"""
        new_user = create_user(email='addmin@gmail.com', password='admin.1234')
        recipe = create_recipe(new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id))

    def test_create_recipe_with_new_tags(self):
        """Crea una nueva receta con nuevas categorias"""
        payload = {
            'title': 'tacos',
            'link': 'https://elamigos.com',
            'description': 'hola mundo',
            'time_minutes': 10,
            'price': Decimal('5.5'),
            'tags': [
                {'name': 'italiana'},
                {'name': 'mexicana'},
                {'name': 'cubana'},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 3)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_existing_tag(self):
        """Crea una nueva receta con nuevas categorias"""
        tag_mexicana = Tag.objects.create(user=self.user, name='Mexicana')
        payload = {
            'title': 'pizza',
            'link': 'https://elamigos.com',
            'description': 'hola mundo',
            'time_minutes': 10,
            'price': Decimal('5.5'),
            'tags': [
                {'name': 'italiana'},
                {'name': 'Mexicana'},
                {'name': 'cubana'},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 3)
        self.assertIn(tag_mexicana, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test crea una nueva categoria cuando se actualice"""
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [
                {'name': 'Desayuno'}
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name='Desayuno')
        self.assertIn(new_tag, recipe.tags.all())

    def test_assign_tag_on_update(self):
        """Test asigna una categoria cuando se actualice"""
        tag_desayuno = Tag.objects.create(user=self.user, name='huevos')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_desayuno)

        tag_almuerzo = Tag.objects.create(user=self.user, name='almuerzo')
        payload = {
            'tags': [{
                'name': 'almuerzo',
            }]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tags = recipe.tags.all()
        self.assertIn(tag_almuerzo, tags)
        self.assertNotIn(tag_desayuno, tags)

    def test_clear_recipe_tags(self):
        """Test eliminando las categorias de la receta"""
        tag = Tag.objects.create(user=self.user, name='huevos')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test crear una receta con nuevos ingredientes"""
        payload = {
            'title': 'tacos',
            'link': 'https://elamigos.com',
            'description': 'hola mundo',
            'time_minutes': 10,
            'price': Decimal('5.5'),
            'ingredientes': [
                {'name': 'sal'},
                {'name': 'azuctar'},
                {'name': 'tortilla'},
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredientes.count(), 3)

        for ingredient_name in payload['ingredientes']:
            exists = Ingredient.objects.filter(
                name=ingredient_name['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test crea la receta con nuevos ingredientes"""
        create_ingredient('carne', self.user)
        create_ingredient('queso', self.user)
        create_ingredient('jamon', self.user)
        payload = {
            'title': 'tacos',
            'link': 'https://elamigos.com',
            'description': 'hola mundo',
            'time_minutes': 10,
            'price': Decimal('5.5'),
            'ingredientes': [
                {'name': 'carne'},
                {'name': 'queso'},
                {'name': 'jamon'},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredientes.count(), 3)
        for ingredient_name in payload['ingredientes']:
            exists = recipe.ingredientes.filter(
                name=ingredient_name['name'], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_update_recipe_with_new_ingredients(self):
        """Test actualizar receta con nuevos ingredientes"""
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredientes': [
                {'name': 'pez'},
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='pez')
        self.assertIn(new_ingredient, recipe.ingredientes.all())

    def test_update_recipe_with_existing_ingredients(self):
        """Test actualizar receta con ingredientes existentes"""
        recipe = create_recipe(user=self.user)
        ingredient_actual = create_ingredient(user=self.user, name='tortillas')

        recipe.ingredientes.add(ingredient_actual)

        nuevo_ingrediente = create_ingredient(user=self.user, name='queso')

        payload = {
            'ingredientes': [
                {'name': 'queso'}
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredientes.count(), 1)
        self.assertIn(nuevo_ingrediente, recipe.ingredientes.all())
        self.assertNotIn(ingredient_actual, recipe.ingredientes.all())

    def test_delete_ingredients_for_recipe(self):
        """Elima ingredientes de la receta"""
        recipe = create_recipe(user=self.user)
        ingredient_actual = create_ingredient(user=self.user, name='zanahoria')

        recipe.ingredientes.add(ingredient_actual)

        payload = {
            'ingredientes': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredientes.count(), 0)
        self.assertNotIn(ingredient_actual, recipe.ingredientes.all())

    def test_filter_by_tags(self):
        """Test filter receta por categorias"""
        """Test filter receta por categorias"""
        recipe_1 = create_recipe(user=self.user)
        recipe_2 = create_recipe(user=self.user)
        categoria_1 = Tag.objects.create(user=self.user, name='Vegan')
        categoria_2 = Tag.objects.create(user=self.user, name='Vegetarian')
        recipe_1.tags.add(categoria_1)
        recipe_2.tags.add(categoria_2)
        recipe_3 = create_recipe(user=self.user)
        params = {'tags': f'{categoria_1.id},{categoria_2.id}'}
        res = self.client.get(RECIPE_URL, params)

        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filter receta por ingredientes"""
        recipe_1 = create_recipe(user=self.user)
        recipe_2 = create_recipe(user=self.user)
        ingredient_1 = create_ingredient(user=self.user, name='carne')
        ingredient_2 = create_ingredient(user=self.user, name='queso')
        recipe_1.ingredientes.add(ingredient_1)
        recipe_2.ingredientes.add(ingredient_2)
        recipe_3 = create_recipe(user=self.user)
        params = {
            'ingredientes': f'{ingredient_1.id},{ingredient_2.id}'
        }
        res = self.client.get(RECIPE_URL, params)
        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)
        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests para subir imagen"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='admin@gmail.com', password='admin.1234'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Prueba subir una imagen a la receta"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
                'image': image_file
            }
            res = self.client.post(url, payload, format='multipart')
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image(self):
        """Prueba subir una imagen invalida"""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'dsdsdsd'}

        res = self.client.post(url, payload, format='multipart')

        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)
