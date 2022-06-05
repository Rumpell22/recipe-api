"""
Comando que valida que la db este lista en django
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Comando que espera que la db este disponible"""

    def handle(self, *args, **options):
        pass