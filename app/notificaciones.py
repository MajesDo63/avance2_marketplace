"""Persist the receipt and send a real confirmation through the configured provider."""
import os
from datetime import datetime, timezone
import boto3
from botocore.config import Config
import requests
from app.db import cursor_db
from app.correo import enviar_real


def cliente_s3():
    return boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'),
                        config=Config(connect_timeout=3, read_timeout=5, retries={'max_attempts': 1}))


def enviar_correo_confirmacion(destinatario, numero_pedido, detalle, total=None):
    # A stable key makes a retry replace the same receipt instead of accumulating copies.
    key = f'comprobantes/pedido_{numero_pedido}.txt'
    content = (f'CONFIRMACIÓN DE PEDIDO #{numero_pedido}\nFecha: {datetime.now(timezone.utc).isoformat()}\n'
               f'Destinatario: {destinatario}\nTotal: {total}\nDetalle: {detalle}\n'
               'Compra de laboratorio: no se realizó ningún cobro ni envío de mercancía.\n')
    cliente_s3().put_object(Bucket=os.environ['S3_BUCKET'], Key=key, Body=content.encode('utf-8'),
                            ContentType='text/plain; charset=utf-8', ServerSideEncryption='AES256')
    # The receipt remains downloadable even when the mail provider is unavailable.
    with cursor_db() as cur:
        cur.execute('UPDATE pedidos SET s3_comprobante_key=%s WHERE id=%s', (key, numero_pedido))
    enviar_real(destinatario, numero_pedido, content)
    # Internal acknowledgement is not proof of email delivery and must not trigger a retry.
    try:
        requests.post(os.environ.get('NOTIF_SERVICE_URL', 'http://notificaciones:5001/notificar'),
                      json={'pedido_id': numero_pedido, 'estado_correo': 'aceptado_por_proveedor'}, timeout=4).raise_for_status()
    except requests.RequestException:
        pass  # nosec B110: mail already accepted; telemetry failure must not resend it.
    return key
