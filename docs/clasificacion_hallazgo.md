# Hallazgo del parche de reenvío de confirmaciones

César Eduardo Valdez Pinto · Al07003448 · Tema 3 Marketplace · 29 de septiembre de 2026

El parche docente consulta un pedido por el identificador de la URL y reenvía su confirmación sin autenticar al solicitante ni comprobar si el pedido le pertenece. Ruta afectada: `POST /pedidos/<id>/reenviar-confirmacion`.

## Tipo y causa

Control de acceso roto: [CWE-306, autenticación ausente](https://cwe.mitre.org/data/definitions/306.html) y [CWE-862, autorización ausente](https://cwe.mitre.org/data/definitions/862.html). Conocer un identificador de pedido no otorga permiso para operar sobre él.

## Severidad justificada

**Media para el parche docente, en el alcance demostrado.** Es explotable remotamente sin sesión. Permite provocar reenvíos al comprador legítimo y diferenciar pedidos existentes; con correo real puede causar mensajes molestos y consumo de cuota. El atacante no puede cambiar el destinatario ni recibe el contenido del pedido. No se demostró robo de comprobantes ni ejecución de comandos; no se justifica llamarlo crítico.

La versión antigua también aceptaba tokens predecibles; ese problema independiente se corrigió con tokens firmados que caducan. No se usa ese segundo fallo para exagerar el impacto del parche original.

## Evidencia y control que lo detectó

El original se aplicó íntegro en una copia aislada dentro de la EC2 QA existente `i-0d077a1e93b366368`. SHA-256: `578f0e41416c23bfe6695179c34e366f024fd10343ed1407d96dd048798b33a8`. Se conserva como texto en `evidencias/parche_docente/reenviar_confirmacion.py.txt`, fuera del código ejecutable.

Se ejecutaron el mismo pipeline y las mismas 37 pruebas sobre ambas versiones. El original falla cuatro pruebas: anónimo obtiene 200 en lugar de 401; otro usuario obtiene 200 en lugar de 403; un token inventado llega a consultar el recurso; un fallo de confirmación devuelve 500 en vez de 503 controlado. La corrección pasa las 37. Las pruebas simulan las dependencias y corren sin red; no envían correos ni modifican pedidos reales.

Gitleaks, Bandit y Trivy no detectaron la autorización faltante. La etapa decisiva es la prueba de comportamiento incorporada al pipeline, no buscar palabras en el código. Reportes completos: `reportes/pipeline_bloqueado.txt` y `reportes/pipeline_verde.txt`. Los reportes anteriores son históricos.

## Falsos positivos

La autorización ausente **no es un falso positivo**: la respuesta 200 en lugar de 401/403 lo demuestra. En una corrida preliminar, Gitleaks marcó un texto de ejemplo de `SECRET_KEY` en `.env.example`. Era un marcador sin uso como credencial. Se dejó el valor vacío con instrucciones para generarlo; no se deshabilitó la regla ni se amplió la exclusión. Después se repitieron ambas corridas completas.
