"""Signed, expiring bearer sessions. Browser credentials are never cookies."""
from functools import wraps
from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='marketplace-cesar-session-v1')


def emitir_token(usuario):
    return serializer().dumps({'id': usuario['id'], 'usuario': usuario['usuario']})


def obtener_usuario_autenticado():
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme != 'Bearer' or not token or len(token) > 2048:
        return None
    try:
        user = serializer().loads(token, max_age=current_app.config.get('TOKEN_MAX_AGE', 7200))
        if not isinstance(user, dict) or type(user.get('id')) is not int or user['id'] < 1:
            return None
        return user
    except (BadSignature, SignatureExpired):
        return None


def autenticado(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        g.usuario = obtener_usuario_autenticado()
        if not g.usuario:
            return jsonify(error='Inicia sesión para continuar.'), 401
        return view(*args, **kwargs)
    return wrapped
