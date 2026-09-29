import json
import os
from decimal import Decimal
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    return psycopg2.connect(host=os.environ['DB_HOST'], dbname=os.getenv('DB_NAME', 'postgres'),
                            user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
                            port=int(os.getenv('DB_PORT', '5432')), connect_timeout=5,
                            sslmode=os.getenv('DB_SSLMODE', 'require'))


@contextmanager
def cursor_db():
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
    finally:
        conn.close()


def obtener_pedido_por_id(pedido_id):
    with cursor_db() as cur:
        cur.execute('SELECT id, usuario_id, correo_comprador, total, detalle, s3_comprobante_key, creado_en FROM pedidos WHERE id=%s', (pedido_id,))
        return cur.fetchone()


def normalizar_items(items):
    if not isinstance(items, list) or not 1 <= len(items) <= 20:
        raise ValueError('El carrito debe tener entre 1 y 20 productos.')
    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Producto inválido.')
        product, quantity = item.get('producto_id'), item.get('cantidad')
        if type(product) is not int or product <= 0 or type(quantity) is not int or not 1 <= quantity <= 99:
            raise ValueError('Revisa los productos y sus cantidades.')
        quantities[product] = quantities.get(product, 0) + quantity
        if quantities[product] > 99:
            raise ValueError('Máximo 99 unidades por producto.')
    return quantities


def preparar_carrito(cur, items, bloquear=False):
    quantities = normalizar_items(items)
    sql = 'SELECT id,nombre,precio,stock FROM productos WHERE id=ANY(%s) ORDER BY id'
    if bloquear:
        sql += ' FOR UPDATE'
    cur.execute(sql, (sorted(quantities),))
    products = cur.fetchall()
    if len(products) != len(quantities):
        raise ValueError('Uno de los productos ya no está disponible.')
    lines, total = [], Decimal('0.00')
    for product in products:
        quantity = quantities[product['id']]
        if product['stock'] < quantity:
            raise ValueError('No hay suficientes existencias de ' + product['nombre'] + '.')
        subtotal = product['precio'] * quantity
        total += subtotal
        lines.append({'producto_id': product['id'], 'nombre': product['nombre'], 'precio': str(product['precio']),
                      'cantidad': quantity, 'subtotal': str(subtotal)})
    return lines, total


def crear_pedido_db(usuario_id, correo, items):
    # Price, ownership and stock are determined here, never trusted from a client.
    with cursor_db() as cur:
        lines, total = preparar_carrito(cur, items, bloquear=True)
        for line in lines:
            cur.execute('UPDATE productos SET stock=stock-%s WHERE id=%s', (line['cantidad'], line['producto_id']))
        detail = json.dumps(lines, ensure_ascii=False)
        cur.execute('INSERT INTO pedidos (usuario_id,correo_comprador,total,detalle) VALUES (%s,%s,%s,%s) RETURNING id',
                    (usuario_id, correo, total, detail))
        order_id = cur.fetchone()['id']
    return {'id': order_id, 'total': str(total), 'detalle': detail}
