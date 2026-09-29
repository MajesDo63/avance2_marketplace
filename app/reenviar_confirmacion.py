from flask import Blueprint, jsonify, current_app
from app.db import obtener_pedido_por_id
from app.notificaciones import enviar_correo_confirmacion
from app.seguridad import obtener_usuario_autenticado

reenviar_bp = Blueprint('reenviar', __name__)


@reenviar_bp.route('/pedidos/<int:pedido_id>/reenviar-confirmacion', methods=['POST'])
def reenviar_confirmacion(pedido_id):
    usuario_autenticado = obtener_usuario_autenticado()
    if not usuario_autenticado:
        return jsonify(error='Inicia sesión para continuar.'), 401
    pedido = obtener_pedido_por_id(pedido_id)
    if pedido is None:
        return jsonify(error='Pedido no encontrado.'), 404
    if pedido['usuario_id'] != usuario_autenticado['id']:
        return jsonify(error='No tienes acceso a este pedido.'), 403
    try:
        key = enviar_correo_confirmacion(pedido['correo_comprador'], pedido['id'], pedido['detalle'], pedido['total'])
    except Exception as exc:
        current_app.logger.warning('Confirmation unavailable: %s', type(exc).__name__)
        return jsonify(error='La confirmación está pendiente. Intenta reenviarla más tarde.'), 503
    return jsonify(mensaje='Confirmación aceptada por el servicio de correo.', pedido_id=pedido_id, comprobante=key), 200
