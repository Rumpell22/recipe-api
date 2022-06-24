"""Vista para la api de usuarios"""
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from .serializers import UserSerializer, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    """Crea un nuevo usuario en el sistema"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Crea un nuevo token para el usuario"""
    serializer_class = AuthTokenSerializer
    # renderer_classes se utiliza para la interfaz web de pruebas drf
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manejo de usuarios auntenticados"""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Regresa el usuario autenticado"""
        return self.request.user
