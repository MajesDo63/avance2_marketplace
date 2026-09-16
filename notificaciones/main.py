import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/salud", methods=["GET"])
def salud():
    return jsonify({"estado": "ok", "servicio": "servicio-notificaciones"}), 200

@app.route("/notificar", methods=["POST"])
def procesar_notificacion():
    data = request.get_json() or {}
    pedido_id = data.get("pedido_id")
    total = data.get("total")
    correo = data.get("correo_cliente")
    
    timestamp = datetime.datetime.utcnow().isoformat()
    log_aviso = f"[{timestamp}] NOTIFICACION EMITIDA -> Pedido #{pedido_id} (${total} USD) confirmado para {correo}"
    print(log_aviso, flush=True)
    
    return jsonify({"estado": "procesado", "confirmacion": log_aviso}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
