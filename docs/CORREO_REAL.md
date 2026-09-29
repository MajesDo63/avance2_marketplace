# Correo real

La aplicación admite SES o SMTP con TLS, sin fallback simulado. Si falta configuración o el proveedor falla, el pedido queda guardado con confirmación pendiente. El comprobante se conserva y puede reenviarse sin repetir la compra.

SES devolvió `AccessDenied` en la cuenta de César el 29 de septiembre de 2026. No se modificaron permisos para evadir la restricción. El correo institucional indicado sirve de destinatario; no concede autorización de envío a la aplicación.

## Configuración privada

En `.env`, configurar `MAIL_PROVIDER=smtp`, `MAIL_FROM`, `SMTP_HOST`, `SMTP_PORT=587` o `465`, `SMTP_USER` y `SMTP_PASSWORD` con credenciales autorizadas por el proveedor. Nunca incluirlas en GitHub o capturas. El puerto 587 exige STARTTLS antes del login; 465 usa TLS desde el inicio. No se admite SMTP sin cifrado. Una cuenta institucional puede requerir OAuth o bloquear contraseña SMTP; este adaptador no implementa OAuth y no se debe debilitar la cuenta para probarlo.

SES requiere `MAIL_PROVIDER=ses`, remitente verificado y rol con permiso de envío. En el sandbox también deben estar verificados los destinatarios: [documentación de AWS](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html).

## Evidencia requerida

Las ocho pruebas de `tests/test_correo.py` simulan los proveedores y no envían mensajes. Una confirmación exitosa significa que el proveedor aceptó el mensaje, no prueba llegada al buzón. La evidencia final requiere compra y reenvío hacia el buzón autorizado y comprobar recepción con fecha y número de pedido.

La integración requiere `QA_EMAIL_DESTINATION` y `QA_ALLOW_REAL_EMAIL=1`, envía dos mensajes reales y limpia solo sus propios registros. No ejecutarla con direcciones inventadas ni sin consentimiento.

Estado: implementación y pruebas unitarias completas; remitente y recepción real pendientes.
