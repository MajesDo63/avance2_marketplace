"""Real transactional mail. No simulation fallback or secrets in logs."""
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
import boto3
from botocore.config import Config


def direccion(value):
    if not isinstance(value, str) or len(value) > 120 or not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}', value):
        raise ValueError('Dirección de correo no válida.')
    return value


def enviar_real(destinatario, pedido_id, contenido):
    recipient = direccion(destinatario)
    sender = direccion(os.environ.get('MAIL_FROM', ''))
    provider = os.environ.get('MAIL_PROVIDER', '').lower()
    subject = f'César Tech | Confirmación del pedido #{int(pedido_id)}'
    if provider == 'ses':
        client = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'us-east-1'),
                              config=Config(connect_timeout=3, read_timeout=8, retries={'total_max_attempts': 1}))
        result = client.send_email(Source=sender, Destination={'ToAddresses': [recipient]},
                                   Message={'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                                            'Body': {'Text': {'Data': contenido, 'Charset': 'UTF-8'}}})
        if not result.get('MessageId'):
            raise RuntimeError('El proveedor no confirmó la aceptación del correo.')
        return result['MessageId']
    if provider != 'smtp':
        raise RuntimeError('Configura MAIL_PROVIDER con ses o smtp para enviar correo real.')
    message = EmailMessage()
    message['From'], message['To'], message['Subject'] = sender, recipient, subject
    message.set_content(contenido)
    host, username, password = (os.environ[key] for key in ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD'))
    if not all((host, username, password)):
        raise RuntimeError('Configuración SMTP incompleta.')
    port = int(os.environ.get('SMTP_PORT', '587'))
    context = ssl.create_default_context()
    if port == 465:
        connection = smtplib.SMTP_SSL(host, port, timeout=10, context=context)
    elif port == 587:
        connection = smtplib.SMTP(host, port, timeout=10)
    else:
        raise ValueError('Usa SMTP con TLS en el puerto 465 o 587.')
    with connection as server:
        if port == 587:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        server.login(username, password)
        refused = server.send_message(message)
        if refused:
            raise RuntimeError('El servidor rechazó el destinatario.')
    return 'aceptado-por-smtp'
