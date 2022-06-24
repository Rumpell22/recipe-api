"""
Serializers para la api de usuarios
"""
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializers para el objeto de usuario"""

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}

    def create(self, validated_data):
        """Create y regresa un usuario con la password encriptada"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Actualiza y regresa el usuario"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializers para el token de los usuarios"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type', 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Valida y logear al usuario"""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = _('Usuario o contrasena invalidos')
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs
