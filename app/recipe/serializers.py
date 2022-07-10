"""
Serializers para la api de receta
"""
from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Serializer para la categoria"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):
    """"Serializer para el ingredient"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializers para la receta"""
    tags = TagSerializer(many=True, required=False)
    ingredientes = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'time_minutes', 'price',
            'link', 'tags', 'ingredientes'
        ]
        read_only_fields = ['id']

    def validate_title(self, data):
        if Recipe.objects.filter(title=data).exists():
            raise serializers.ValidationError(
                {'error': 'Ya existe una receta con este nombre'}
            )
        return data

    def _get_or_create_tags(self, tags, recipe):
        """Crea o actualiza categorias"""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Crea u obtiene ingredientes"""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient, obj = Ingredient.objects.get_or_create(
                user=auth_user, **ingredient
            )
            recipe.ingredientes.add(ingredient)

    def create(self, validated_data):
        """Crea la receta"""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredientes', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Actualiza la receta"""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredientes', [])
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredientes.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer para el retrieve de la receta"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializar para subir imagen a la receta"""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': True}}
