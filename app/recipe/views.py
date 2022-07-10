"""
Vistas de la api de recetas
"""
from symbol import parameters

from drf_spectacular.utils import extend_schema_view, \
    OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Recipe, Tag, Ingredient
from recipe import serializers

@extend_schema_view(
        list=extend_schema(
            parameters=[
                OpenApiParameter(
                    'tags',
                    OpenApiTypes.STR,
                    description='Valores id de la categoria separados por comas '
                ),
                OpenApiParameter(
                    'ingredientes',
                    OpenApiTypes.STR,
                    description='Valores id de los ingredientes separados por coma'
                )
            ]
        )
    )
class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset para los apis de recetas"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, list):
        """Convierte una lista de strings a enteros"""
        return [int(str_id) for str_id in list.split(",")]


    def get_queryset(self):
        """Metodo get"""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredientes')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredientes__id__in=ingredients_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Regresa el serializer en base a la request"""
        if self.action == 'list':
            return serializers.RecipeSerializer
        if self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Crea un nueva receta"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Subir una imagen a la receta"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0,1],
                description='Filtra los items asignados a la receta'
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """"Base viewset for recipe atributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Metodo get(filtra)"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only',0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """ViewSet para las categorias"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """API para los ingredientes"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
