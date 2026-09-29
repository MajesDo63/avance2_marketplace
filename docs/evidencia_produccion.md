# Evidencia de Producción

El 29 de septiembre de 2026 se creó y desplegó una instancia nueva para César, después de que el pipeline completo aprobara el código corregido. La instancia QA original se conservó.

| Dato | QA | Producción |
|---|---|---|
| EC2 | i-0d077a1e93b366368 | i-02c5f6fbbbcae6fe0 |
| Nombre | InstanciaQA | Cesar-Tech-Produccion |
| URL al verificar | http://44.202.249.26:5000/ | http://54.204.91.37:5000/ |
| Base de datos | postgres | marketplace_prod |
| Bucket privado | marketplace-datos-protegidos-cesar-lsca2314 | cesar-tech-produccion-940828937790 |

Cuenta de ambos ambientes: `940828937790`; región `us-east-1`. Producción es una t2.micro con disco gp3 cifrado de 12 GiB e IMDSv2 obligatorio. Solo se expone el puerto web 5000 y SSH se limita a la IP de mantenimiento. El servicio interno de notificaciones no publica su puerto. Se autorizó únicamente el grupo de seguridad nuevo hacia el puerto PostgreSQL del RDS existente.

La base de Producción es distinta y se inició con 33 productos, cero usuarios y cero pedidos. Comparte el servidor RDS del laboratorio para no crear un segundo servidor de base de datos. No se copiaron cuentas ni compras de QA. Los comprobantes de ambos ambientes van a buckets distintos para que no colisionen sus números de pedido.

## Comprobaciones efectuadas

`reportes/version_aprobada.sha256` identifica el código, plantillas, recursos, pruebas y configuración pública aprobados en QA. En Producción se verificó cada hash antes de activar la última imagen. Después se ejecutaron las 37 pruebas sobre la imagen desplegada y `/salud` informó conexión con RDS, S3 y el servicio de notificaciones. La página se abrió en el navegador usando la IP de Producción. Salida operativa completa: `reportes/produccion_verificada.txt`.

## Limitaciones declaradas

El correo real sigue pendiente de un remitente autorizado; SES está bloqueado por AWS Academy. Las pruebas unitarias simulan al proveedor. No se afirma que una confirmación haya llegado al buzón. El sitio académico usa HTTP y compras sin cobro.

La captura de la consola AWS debe corresponder a la cuenta de César, no a la sesión del compañero. La evidencia de terminal y la página no sustituyen esa captura específica si el profesor la exige. Las IP pueden cambiar tras un reinicio del laboratorio. Revisar el estado antes de la entrega y apagar los recursos cuando se termine la demostración; no se ha terminado ninguna instancia automáticamente.
