import os
import secrets
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch
os.environ.setdefault('SECRET_KEY', secrets.token_urlsafe(48))
from app.main import app
from app.seguridad import emitir_token, serializer
from app.db import normalizar_items, preparar_carrito, crear_pedido_db


class QAControls(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with app.app_context():
            self.token = emitir_token({'id': 12, 'usuario': 'qa_unit'})
        self.headers = {'Authorization': 'Bearer ' + self.token}
        self.order = {'id': 987, 'usuario_id': 12, 'correo_comprador': 'qa@example.invalid', 'total': Decimal('75'), 'detalle': 'Prueba', 's3_comprobante_key': 'comprobantes/pedido_987.txt'}

    def test_session_has_signature(self):
        with app.app_context():
            self.assertEqual(serializer().loads(self.token)['id'], 12)
        self.assertNotIn('token-seguro-usr-', self.token)

    def test_tampered_session_is_rejected(self):
        response = self.client.get('/pedidos', headers={'Authorization': 'Bearer x' + self.token})
        self.assertEqual(response.status_code, 401)

    def test_expired_session_is_rejected(self):
        with patch.dict(app.config, {'TOKEN_MAX_AGE': -1}):
            self.assertEqual(self.client.get('/pedidos', headers=self.headers).status_code, 401)

    def test_protected_routes_do_not_access_database_anonymously(self):
        with patch('app.db.get_connection') as db:
            for method, path in [('get','/pedidos'), ('get','/pedidos/987/comprobante'), ('post','/productos'), ('post','/carrito')]:
                self.assertEqual(getattr(self.client, method)(path, json={}).status_code, 401)
        db.assert_not_called()

    def test_owner_can_resend(self):
        with patch('app.reenviar_confirmacion.obtener_pedido_por_id', return_value=self.order), patch('app.reenviar_confirmacion.enviar_correo_confirmacion', return_value='receipt') as notify:
            response=self.client.post('/pedidos/987/reenviar-confirmacion', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        notify.assert_called_once()

    def test_other_user_cannot_resend(self):
        order={**self.order, 'usuario_id': 99}
        with patch('app.reenviar_confirmacion.obtener_pedido_por_id', return_value=order), patch('app.reenviar_confirmacion.enviar_correo_confirmacion') as notify:
            response=self.client.post('/pedidos/987/reenviar-confirmacion', headers=self.headers)
        self.assertEqual(response.status_code, 403)
        notify.assert_not_called()

    def test_anonymous_cannot_resend(self):
        with patch('app.reenviar_confirmacion.obtener_pedido_por_id') as find, patch('app.reenviar_confirmacion.enviar_correo_confirmacion') as notify:
            response=self.client.post('/pedidos/987/reenviar-confirmacion')
        self.assertEqual(response.status_code,401)
        find.assert_not_called(); notify.assert_not_called()

    def test_missing_order_is_404(self):
        with patch('app.reenviar_confirmacion.obtener_pedido_por_id', return_value=None):
            self.assertEqual(self.client.post('/pedidos/987/reenviar-confirmacion', headers=self.headers).status_code,404)

    def test_other_user_cannot_read_receipt(self):
        with patch('app.main.obtener_pedido_por_id', return_value={**self.order,'usuario_id':99}), patch('app.main.cliente_s3') as s3:
            self.assertEqual(self.client.get('/pedidos/987/comprobante',headers=self.headers).status_code,404)
        s3.assert_not_called()

    def test_confirmation_failure_is_reported(self):
        with patch('app.reenviar_confirmacion.obtener_pedido_por_id', return_value=self.order), patch('app.reenviar_confirmacion.enviar_correo_confirmacion', side_effect=RuntimeError('sensitive details')):
            response=self.client.post('/pedidos/987/reenviar-confirmacion',headers=self.headers)
        self.assertEqual(response.status_code,503)
        self.assertNotIn('sensitive',response.get_data(as_text=True))

    def test_checkout_uses_signed_owner_and_server_total(self):
        data={'usuario_id':99,'total':0.01,'correo':'qa@example.invalid','items':[{'producto_id':1,'cantidad':1}]}
        with patch('app.main.crear_pedido_db',return_value={'id':987,'total':'75.00','detalle':'Prueba'}) as create, patch('app.main.enviar_correo_confirmacion'):
            response=self.client.post('/ordenes/checkout',json=data,headers=self.headers)
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json['total'],'75.00')
        create.assert_called_once_with(12,'qa@example.invalid',data['items'])

    def test_notification_failure_does_not_hide_saved_order(self):
        with patch('app.main.crear_pedido_db',return_value={'id':987,'total':'75.00','detalle':'Prueba'}) as create, patch('app.main.enviar_correo_confirmacion',side_effect=RuntimeError):
            response=self.client.post('/ordenes/checkout',json={'correo':'qa@example.invalid','items':[{'producto_id':1,'cantidad':1}]},headers=self.headers)
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json['confirmacion'],'pendiente')
        create.assert_called_once()

    def test_invalid_checkout_email_never_writes(self):
        with patch('app.main.crear_pedido_db') as create:
            self.assertEqual(self.client.post('/ordenes/checkout',json={'correo':'invalid'},headers=self.headers).status_code,400)
        create.assert_not_called()

    def test_login_rejects_missing_or_non_string_fields(self):
        with patch('app.main.cursor_db') as db:
            for data in [{},{'usuario':{},'password':[]},[]]:
                self.assertEqual(self.client.post('/login',json=data).status_code,400)
        db.assert_not_called()

    def test_registration_requires_long_password(self):
        with patch('app.main.cursor_db') as db:
            self.assertEqual(self.client.post('/registro',json={'usuario':'qa_test','password':'short'}).status_code,400)
        db.assert_not_called()

    def test_publish_rejects_invalid_prices(self):
        with patch('app.main.cursor_db') as db:
            for value in ['NaN','Infinity','-1','0','1.234',None]:
                self.assertEqual(self.client.post('/productos',json={'nombre':'QA product','precio':value,'stock':2},headers=self.headers).status_code,400)
        db.assert_not_called()

    def test_publish_rejects_negative_or_fractional_stock(self):
        for stock in [-1,1.5,True]:
            self.assertEqual(self.client.post('/productos',json={'nombre':'QA product','precio':'1.00','stock':stock},headers=self.headers).status_code,400)

    def test_health_dependency_failure_is_not_healthy(self):
        with patch('app.main.get_connection',side_effect=RuntimeError('secret')), patch('app.main.cliente_s3'), patch('app.main.requests.get') as get:
            get.return_value.json.return_value={'estado':'ok'}
            response=self.client.get('/salud')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json['estado'],'degradado')
        self.assertNotIn('secret',response.get_data(as_text=True))

    def test_security_headers_and_template(self):
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertIn('Marketplace César',response.get_data(as_text=True))
        self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
        self.assertEqual(response.headers['Cache-Control'],'no-store')


class CartTransactions(unittest.TestCase):
    def test_quantities_must_be_positive_integers(self):
        for amount in [0,-1,1.5,True,100,'1']:
            with self.assertRaises(ValueError): normalizar_items([{'producto_id':1,'cantidad':amount}])

    def test_duplicate_items_are_combined(self):
        self.assertEqual(normalizar_items([{'producto_id':1,'cantidad':2},{'producto_id':1,'cantidad':3}]),{1:5})

    def test_empty_cart_is_rejected(self):
        with self.assertRaises(ValueError): normalizar_items([])

    def test_stock_and_price_are_read_from_database(self):
        cur=MagicMock();cur.fetchall.return_value=[{'id':1,'nombre':'QA','precio':Decimal('12.50'),'stock':2}]
        lines,total=preparar_carrito(cur,[{'producto_id':1,'cantidad':2,'precio':0.01}],bloquear=True)
        self.assertEqual(total,Decimal('25.00'))
        self.assertIn('FOR UPDATE',cur.execute.call_args.args[0])

    def test_insufficient_stock_is_rejected(self):
        cur=MagicMock();cur.fetchall.return_value=[{'id':1,'nombre':'QA','precio':Decimal('12.50'),'stock':1}]
        with self.assertRaises(ValueError): preparar_carrito(cur,[{'producto_id':1,'cantidad':2}])

    def test_purchase_stock_and_order_share_transaction(self):
        conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
        cur.fetchall.return_value=[{'id':1,'nombre':'QA','precio':Decimal('12.50'),'stock':2}]
        cur.fetchone.return_value={'id':987}
        with patch('app.db.get_connection',return_value=conn): result=crear_pedido_db(12,'qa@example.invalid',[{'producto_id':1,'cantidad':1}])
        self.assertEqual(result['total'],'12.50')
        self.assertEqual(len(cur.execute.call_args_list),3)
        conn.__exit__.assert_called_once_with(None,None,None)
        conn.close.assert_called_once()

    def test_stock_failure_rolls_back_and_closes_connection(self):
        conn=MagicMock();cur=conn.cursor.return_value.__enter__.return_value
        cur.fetchall.return_value=[{'id':1,'nombre':'QA','precio':Decimal('12.50'),'stock':0}]
        with patch('app.db.get_connection',return_value=conn),self.assertRaises(ValueError): crear_pedido_db(12,'qa@example.invalid',[{'producto_id':1,'cantidad':1}])
        self.assertIs(conn.__exit__.call_args.args[0],ValueError)
        conn.close.assert_called_once()


if __name__=='__main__':
    unittest.main(verbosity=2)
