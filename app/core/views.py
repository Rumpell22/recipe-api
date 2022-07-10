"""
Vistas simples del core
"""
from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(['GET'])
def check_health(request):
    """Regresa una respuesta de exito"""
    return Response('Server funcionando correctamente')