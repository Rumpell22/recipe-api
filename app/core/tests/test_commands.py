"""
Test comandos custom de django
"""
from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase
from psycopg2 import OperationalError as Psycopg2Error


@patch("core.managment.commands.wait_for_db.Command.check")
class CommandTest(SimpleTestCase):
    """Test de los comandos"""

    def test_wait_for_db_ready(self, patched_check):
        """Prueba la espera hacia la base de datos"""
        patched_check.return_value = True
        call_command('wait_for_db')
        patched_check.assert_called_once_with(database=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patch_sleep, patched_check):
        """Prueba que se vuelva a conectar cuando ocurra un error"""
        patched_check.side_effect = [Psycopg2Error] * 2 \
                                    + [OperationalError] * 3 + [True]
        call_command('wait_for_db')
        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(database=['default'])
