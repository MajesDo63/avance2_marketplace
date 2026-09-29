import os
import re
from decimal import Decimal, InvalidOperation
import psycopg2
import requests
from flask import Flask, Response, g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_connection, cursor_db, crear_pedido_db, preparar_carrito, obtener_pedido_por_id
from app.notificaciones import cliente_s3, enviar_correo_confirmacion
from app.reenviar_confirmacion import reenviar_bp
from app.seguridad import autenticado, emitir_token
from app.correo import direccion

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY'), MAX_CONTENT_LENGTH=32768, TOKEN_MAX_AGE=7200)
if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY']) < 32:
    raise RuntimeError('SECRET_KEY debe configurarse con al menos 32 caracteres aleatorios.')
app.register_blueprint(reenviar_bp)


def datos_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Envía un objeto JSON válido.')
    return data


@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    if not request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(psycopg2.Error)
def database_error(error):
    app.logger.warning('Database request failed: %s', type(error).__name__)
    return jsonify(error='La base de datos no pudo completar la operación. Intenta más tarde.'), 503


@app.errorhandler(Exception)
def unexpected_error(error):
    if isinstance(error, HTTPException):
        return jsonify(error=error.description), error.code
    app.logger.error('Request failed: %s', type(error).__name__)
    return jsonify(error='No se pudo completar la operación.'), 500


@app.get('/')
def inicio():
    return render_template('index.html')


@app.get('/salud')
def salud():
    state = {}
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
        finally:
            conn.close()
        state['base_datos_rds'] = 'conectado'
    except Exception:
        state['base_datos_rds'] = 'no_disponible'
    try:
        cliente_s3().head_bucket(Bucket=os.environ['S3_BUCKET'])
        state['almacenamiento_s3'] = 'conectado'
    except Exception:
        state['almacenamiento_s3'] = 'no_disponible'
    try:
        url = os.environ.get('NOTIF_SERVICE_URL', 'http://notificaciones:5001/notificar').rsplit('/', 1)[0] + '/salud'
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        state['notificaciones'] = 'conectado' if response.json().get('estado') == 'ok' else 'no_disponible'
    except Exception:
        state['notificaciones'] = 'no_disponible'
    ok = all(v == 'conectado' for v in state.values())
    return jsonify(estado='ok' if ok else 'degradado', servicio='marketplace-api', **state), 200 if ok else 503


@app.post('/registro')
def registro():
    data = datos_json()
    usuario, password = data.get('usuario'), data.get('password')
    if not isinstance(usuario, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{3,50}', usuario):
        raise ValueError('Usuario: entre 3 y 50 letras, números, puntos, guiones o guiones bajos.')
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise ValueError('La contraseña debe tener entre 12 y 128 caracteres.')
    hashed = generate_password_hash(password)
    try:
        with cursor_db() as cur:
            cur.execute('INSERT INTO usuarios (usuario,password_hash) VALUES (%s,%s) RETURNING id', (usuario, hashed))
            user_id = cur.fetchone()['id']
    except psycopg2.errors.UniqueViolation:
        return jsonify(error='Ese nombre de usuario ya existe.'), 409
    return jsonify(mensaje='Cuenta creada. Ya puedes iniciar sesión.', usuario_id=user_id), 201


@app.post('/login')
def login():
    data = datos_json()
    usuario, password = data.get('usuario'), data.get('password')
    if not isinstance(usuario, str) or not isinstance(password, str) or not 1 <= len(usuario) <= 50 or not 1 <= len(password) <= 128:
        raise ValueError('Escribe tu usuario y contraseña.')
    with cursor_db() as cur:
        cur.execute('SELECT id,usuario,password_hash FROM usuarios WHERE usuario=%s', (usuario,))
        user = cur.fetchone()
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify(error='Usuario o contraseña incorrectos.'), 401
    return jsonify(mensaje='Sesión iniciada.', token_sesion=emitir_token(user), usuario_id=user['id'], usuario=user['usuario'])


@app.get('/productos')
def productos():
    with cursor_db() as cur:
        cur.execute('SELECT id,nombre,precio,stock FROM productos ORDER BY id')
        return jsonify(catalogo=cur.fetchall())


@app.post('/productos')
@autenticado
def publicar_producto():
    data = datos_json()
    nombre, stock = data.get('nombre'), data.get('stock')
    if not isinstance(nombre, str) or not 3 <= len(nombre.strip()) <= 100:
        raise ValueError('El nombre debe tener entre 3 y 100 caracteres.')
    if type(stock) is not int or not 0 <= stock <= 10000:
        raise ValueError('Las existencias deben ser un entero entre 0 y 10000.')
    try:
        precio = Decimal(str(data.get('precio')))
        if not precio.is_finite() or not Decimal('0.01') <= precio <= Decimal('999999.99') or precio != precio.quantize(Decimal('0.01')):
            raise ValueError('El precio debe ser positivo y tener hasta dos decimales.')
    except (InvalidOperation, TypeError):
        raise ValueError('Escribe un precio válido.') from None
    with cursor_db() as cur:
        cur.execute('INSERT INTO productos (nombre,precio,stock) VALUES (%s,%s,%s) RETURNING id', (nombre.strip(), precio, stock))
        product_id = cur.fetchone()['id']
    return jsonify(mensaje='Producto publicado.', producto_id=product_id), 201


@app.post('/carrito')
@autenticado
def carrito():
    with cursor_db() as cur:
        lines, total = preparar_carrito(cur, datos_json().get('items'))
    return jsonify(items=lines, total=str(total))


@app.post('/ordenes/checkout')
@autenticado
def checkout():
    data = datos_json()
    correo = data.get('correo')
    direccion(correo)
    order = crear_pedido_db(g.usuario['id'], correo, data.get('items'))
    confirmation = 'confirmada'
    try:
        enviar_correo_confirmacion(correo, order['id'], order['detalle'], order['total'])
    except Exception as exc:
        app.logger.warning('Order %s confirmation pending: %s', order['id'], type(exc).__name__)
        confirmation = 'pendiente'
    return jsonify(mensaje='Pedido registrado.', pedido_id=order['id'], total=order['total'], confirmacion=confirmation,
                   simulacion=True, correo='aceptado_por_proveedor' if confirmation == 'confirmada' else 'pendiente'), 201


@app.get('/pedidos')
@autenticado
def pedidos():
    with cursor_db() as cur:
        cur.execute('SELECT id,correo_comprador,total,detalle,s3_comprobante_key,creado_en FROM pedidos WHERE usuario_id=%s ORDER BY id DESC LIMIT 50', (g.usuario['id'],))
        return jsonify(pedidos=cur.fetchall())


@app.get('/pedidos/<int:pedido_id>/comprobante')
@autenticado
def comprobante(pedido_id):
    order = obtener_pedido_por_id(pedido_id)
    if not order or order['usuario_id'] != g.usuario['id']:
        return jsonify(error='Comprobante no encontrado.'), 404
    if not order['s3_comprobante_key']:
        return jsonify(error='Confirmación pendiente. Utiliza Reenviar confirmación.'), 409
    result = cliente_s3().get_object(Bucket=os.environ['S3_BUCKET'], Key=order['s3_comprobante_key'])
    with result['Body'] as body:
        content = body.read(1_048_576)
    return Response(content, content_type='text/plain; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="pedido-{pedido_id}.txt"'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # nosec B104: exposed only by the existing QA port.
