"""
Comando que valida que la db este lista en django
"""
import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2Error


class Command(BaseCommand):
    """Comando que espera que la db este disponible"""

    def handle(self, *args, **options):
        """Entrypoint para los comandos"""
        self.stdout.write('Esperando base de datos....')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Base de datos no disponible,'
                                  'esperando un segundo')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Base de datos disponible'))
