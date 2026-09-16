# Marketplace Distribuido Seguro (Avance 2)

**Estudiante:** César Eduardo Valdez Pinto
**Materia:** LSCA2314 - Herramientas de Tecnologías de Información
**Entorno:** AWS Academy (EC2, S3, RDS PostgreSQL)

---

## 1. Arquitectura del Sistema
* **API Principal (app/):** Desarrollada en Python con Flask y servida con Gunicorn en el puerto 5000. Endpoints: `/registro`, `/login`, `/productos`, `/carrito`, `/ordenes/checkout` y `/salud`.
* **Microservicio de Notificaciones (notificaciones/):** Servicio desacoplado en el puerto 5001. Recibe confirmaciones de ordenes asincronas via HTTP POST.
* **Red de Contenedores:** Red bridge privada `avance2_marketplace` en Docker Compose con usuarios no root (`appuser`) y `HEALTHCHECK`.
* **Infraestructura Cloud (AWS):**
  * S3: Bucket privado con cifrado SSE-S3 (AES-256) y bloqueo publico activo.
  * RDS: PostgreSQL en subred privada sin direccion IP publica y cifrado KMS.

---

## 2. Despliegue y Pruebas
1. Levantar contenedores: `docker-compose up --build -d`
2. Validar salud: `curl http://localhost:5000/salud` y `curl http://localhost:5001/salud`
3. Flujo transaccional: registro, login, catalogo, carrito y checkout.
4. Logs desacoplados: `docker-compose logs notificaciones`

---

## 3. Pipeline DevSecOps
Ejecucion: `./pipeline/ejecutar_pipeline.sh`
* `reportes/corrida_roja.txt`: Bloqueo ante hallazgos reales HIGH (Bandit B104 e IaC).
* `reportes/corrida_verde.txt`: Veredicto [PERMITIDO] tras remediacion.
* `reportes/sbom_cyclonedx.json`: Inventario de software CycloneDX.
