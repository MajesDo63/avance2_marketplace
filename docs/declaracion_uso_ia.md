# Declaración Obligatoria sobre el Uso de Inteligencia Artificial

**Estudiante:** César Eduardo Valdez Pinto  
**Curso:** LSCA2314 - Herramientas de Tecnologías de Información  
**Periodo:** AD26  
**Proyecto:** El Reto - Avance 2 (Marketplace)

---

## 1. Herramientas de IA Utilizadas
* **Modelo / Asistente:** Asistente de IA colaborativo.
* **Propósito:** Generación de esqueletos de código base, configuración de sintaxis en Terraform y asistencia en la depuración de reglas de escáneres de seguridad.

---

## 2. Componentes Asistidos por IA
* **Código de la API y Microservicio:** Generación de la estructura REST inicial de Flask para la autenticación, catálogo y llamada al microservicio de notificaciones.
* **Plantilla de Terraform (`infra/main.tf`):** Definición de bloques HCL para S3 y RDS con directivas de cifrado.
* **Script de Pipeline (`pipeline/ejecutar_pipeline.sh`):** Estructuración de la compuerta de decisión final integrada y redirección de bitácoras.

---

## 3. Auditoría, Pruebas y Correcciones Realizadas por el Alumno
* **Depuración de dependencias de sistema:** La IA asumió la presencia de paquetes globales que no existían en Amazon Linux (`pip3`, `gitleaks`, `trivy`, `bandit`), requiriendo la instalación manual de repositorios y binarios en la máquina virtual EC2.
* **Remediación del hallazgo Bandit CWE-605 / B104:** Se identificó que la llamada de desarrollo `app.run(host="0.0.0.0")` generaba una alerta media en el análisis SAST; se corrigió manualmente sustituyéndola por `127.0.0.1` para restringir la escucha a la interfaz de loopback.
* **Gestión de excepción Trivy (AVD-AWS-0132):** Se detectó que Trivy bloqueaba la infraestructura por no usar claves CMK de KMS. Se analizó la limitación de privilegios del rol `LabRole` de AWS Academy y se documentó formalmente la regla en `.trivyignore` justificando el uso de `SSE-S3 (AES-256)`.
* **Pruebas de comunicación entre contenedores:** Validación directa en consola mediante comandos `curl` a endpoints locales y monitoreo de logs con `docker-compose logs` para corroborar el desacoplamiento efectivo.
