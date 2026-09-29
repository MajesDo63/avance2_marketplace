# Estado de la entrega de César

Código de remediación publicado: [fb34ce32dbd7cf7e4cd779d96c4b5d6cd466bfba](https://github.com/MajesDo63/avance2_marketplace/commit/fb34ce32dbd7cf7e4cd779d96c4b5d6cd466bfba).

## Trabajo comprobado

- Se conservó la EC2 QA del Avance 2 y sus usuarios, compras y existencias.
- Se ejecutó el parche exacto del docente en una copia aislada dentro de QA: el pipeline bloqueó cuatro pruebas fallidas.
- La corrección pasó las 37 pruebas y las etapas completas de secretos, SAST, IaC y SBOM. El original docente conserva su SHA-256.
- Se creó la EC2 de Producción `i-02c5f6fbbbcae6fe0`, con base y bucket separados. Sus 37 archivos aprobados coinciden por hash; las pruebas también se ejecutaron en la imagen de Producción.
- Se comprobaron la página, RDS, S3 y el servicio interno. La base de Producción comenzó con 33 productos y sin copiar usuarios o pedidos.
- Se publicaron código, clasificación, respuesta al incidente, declaración de IA y reportes. La revisión de secretos no detectó credenciales en el contenido publicado.

## Evidencias visuales

Las capturas `01_rojo` a `06_produccion` muestran salidas reales en un visor local; no son capturas de la consola AWS. Los reportes originales se conservan en `reportes/`. La evidencia de terminal para Producción se usa por instrucción del solicitante; el docente puede exigir además su captura específica de la consola.

La captura `07_produccion` corresponde a la página de la nueva EC2. `03_github_publicado` muestra el repositorio después de publicar la remediación.

## Documento de plataforma

[Evidencias_Cesar_Al07003448.docx](Evidencias_Cesar_Al07003448.docx) conserva la estructura de la plantilla, incluye nombre, matrícula, commit, siete imágenes, autoevaluación y explicaciones. Se validó su estructura y se inspeccionaron las imágenes originales. Falta revisar la distribución final de páginas en Word porque el conversor de documentos no está disponible en este entorno. La reflexión identifica configurar el pipeline como lo más difícil, según la respuesta facilitada; la respuesta hipotética de la última sección se propone para revisión de César.

## Lo que no está acreditado

No se ha demostrado recepción de correo real. SES está denegado por AWS Academy y no hay remitente SMTP configurado. SNS se exploró como alternativa, pero se canceló por indicación del solicitante; su canal fue eliminado antes de enviar mensajes de pedidos. Esto no debe marcarse como correo real completo ante el profesor.

No se modificó la cuenta AWS del otro proyecto. Las dos instancias de César permanecen encendidas para revisión; no se terminaron automáticamente. Sus IP pueden cambiar al reiniciar el laboratorio.
