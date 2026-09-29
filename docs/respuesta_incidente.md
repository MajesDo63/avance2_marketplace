# Contención y prevención

## Contención inmediata

El parche vulnerable se ejecutó en una copia aislada en la misma instancia QA, en un contenedor de pruebas sin red ni puertos publicados. No se reemplazó la aplicación pública con el parche vulnerable. El pipeline bloqueó su promoción. Se conservaron el original, su hash y la salida completa.

Si esa versión estuviera expuesta en un servicio real, se desactivaría temporalmente el reenvío o restringiría la ruta mientras se revisan registros y se prepara el arreglo. Es una medida propuesta; no se afirma haber instalado un WAF o un balanceador en el laboratorio.

## Prevención implementada

La ruta autentica una sesión firmada y vigente antes de consultar la base. Compara `pedido.usuario_id` con la identidad autenticada antes de llamar al correo. Devuelve 401 sin sesión válida y 403 para un pedido ajeno; el propietario conserva el reenvío. Un identificador en el cuerpo de la petición nunca sustituye esa autorización.

El pipeline comprueba los casos anónimo, token inventado, otro usuario y propietario, y que un rechazo no envía correo. También prueba errores del proveedor, inyección de cabeceras y TLS antes del login SMTP. Si falla la confirmación no se crea otra compra: el pedido y comprobante permanecen y el reenvío informa 503.

## Alcance operativo

La recepción en el buzón no se considera demostrada por pruebas unitarias o un acuse interno. AWS Academy denegó SES; falta configurar un remitente SMTP autorizado y verificar recepción real. La aplicación no sustituye ese requisito con una simulación.

En un servicio real se añadirían HTTPS público, límites de frecuencia, verificación de destinatarios y una cola durable con seguimiento de entrega. No se presentan esas mejoras como ya implementadas.
