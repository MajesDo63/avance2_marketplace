"""Regression checks: no database writes or real notifications."""
import unittest
import os
import secrets
from unittest.mock import patch
os.environ.setdefault('SECRET_KEY', secrets.token_urlsafe(48))
from app.main import app


class QARegressions(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_pagina_principal_disponible(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_token_inventado_no_autentica(self):
        with patch('app.reenviar_confirmacion.obtener_pedido_por_id', return_value=None):
            response = self.client.post('/pedidos/2147483647/reenviar-confirmacion', headers={'Authorization': 'Bearer token-seguro-usr-1'})
        self.assertEqual(response.status_code, 401)

    def test_compra_anonima_no_escribe_ni_notifica(self):
        with patch('app.main.crear_pedido_db', return_value=999999) as create, patch('app.main.enviar_correo_confirmacion', return_value=True) as notify:
            response = self.client.post('/ordenes/checkout', json={'usuario_id': 1, 'total': 0.01})
        self.assertEqual(response.status_code, 401)
        create.assert_not_called()
        notify.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
