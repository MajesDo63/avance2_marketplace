import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "marketplace_db")
DB_USER = os.getenv("DB_USER", "postgres")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "mi-marketplace-bucket")
NOTIF_SERVICE_URL = os.getenv("NOTIF_SERVICE_URL", "http://notificaciones:5001/notificar")

USUARIOS = {}
PRODUCTOS = [
    {"id": 1, "nombre": "Teclado Mecanico", "precio": 75.0, "stock": 10},
    {"id": 2, "nombre": "Mouse Inalambrico", "precio": 45.0, "stock": 25},
    {"id": 3, "nombre": "Monitor 24 pulg", "precio": 180.0, "stock": 5}
]
CARRITO = []

@app.route("/salud", methods=["GET"])
def salud():
    return jsonify({"estado": "ok", "servicio": "marketplace-api"}), 200

@app.route("/registro", methods=["POST"])
def registro():
    data = request.get_json() or {}
    usuario = data.get("usuario")
    password = data.get("password")
    if not usuario or not password:
        return jsonify({"error": "Faltan credenciales"}), 400
    USUARIOS[usuario] = password
    return jsonify({"mensaje": f"Usuario {usuario} registrado exitosamente"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    usuario = data.get("usuario")
    password = data.get("password")
    if USUARIOS.get(usuario) == password:
        return jsonify({"mensaje": "Autenticacion correcta", "token_sesion": "token-simulado-xyz"}), 200
    return jsonify({"error": "Credenciales invalidas"}), 401

@app.route("/productos", methods=["GET"])
def listar_productos():
    return jsonify({"catalogo": PRODUCTOS}), 200

@app.route("/carrito", methods=["POST"])
def agregar_carrito():
    data = request.get_json() or {}
    producto_id = data.get("producto_id")
    producto = next((p for p in PRODUCTOS if p["id"] == producto_id), None)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    CARRITO.append(producto)
    return jsonify({"mensaje": "Producto agregado", "carrito_actual": CARRITO}), 200

@app.route("/ordenes/checkout", methods=["POST"])
def checkout():
    if not CARRITO:
        return jsonify({"error": "El carrito esta vacio"}), 400
    total = sum(p["precio"] for p in CARRITO)
    pedido_id = len(CARRITO) + 1000

    payload_notificacion = {
        "pedido_id": pedido_id,
        "total": total,
        "articulos": len(CARRITO),
        "correo_cliente": "cliente_prueba@dominio.com"
    }

    try:
        resp = requests.post(NOTIF_SERVICE_URL, json=payload_notificacion, timeout=3)
        notif_status = resp.json().get("estado", "desconocido")
    except Exception as e:
        notif_status = f"falla_envio: {str(e)}"

    CARRITO.clear()
    return jsonify({
        "mensaje": "Pedido confirmado con exito",
        "pedido_id": pedido_id,
        "total": total,
        "servicio_notificacion": notif_status
    }), 201

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
