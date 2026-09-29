# Tabla de Decisiones y Justificación del Pipeline DevSecOps

**Aplicación:** Marketplace Distribuido (API Flask + Microservicio de Notificaciones)  
**Entorno de Despliegue:** AWS Academy (EC2, S3, RDS PostgreSQL)  
**Umbral Global Integrado:** Bloqueo preventivo ante cualquier hallazgo de severidad HIGH o CRITICAL.

---

## 1. Matriz de Controles y Justificación de Riesgos

| Etapa del Pipeline | Herramienta Seleccionada | Tipo de Análisis | Riesgo Concreto del Marketplace que Mitiga | Justificación del Umbral Elegido | Lo que se decidió NO cubrir y por qué técnico |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Detección de Secretos** | Gitleaks (v8.18) | Escaneo de Credenciales | Exposición accidental de contraseñas maestras de RDS (`dbadmin`), cadenas de conexión o credenciales temporales de AWS Academy en el código del carrito y autenticación. | **Cero tolerancia (bloqueo inmediato con 1 secreto):** Una sola credencial expuesta en un repositorio público o compartido compromete toda la infraestructura cloud del Marketplace. | No se bloquea por palabras clave en comentarios (`PENDIENTE: agregar credencial`) para evitar falsos positivos que frenen el desarrollo continuo. |
| **2. SAST (Código Python)** | Bandit (v1.8) | Análisis Estático de Código Fuente | Enlaces inseguros de interfaz (`0.0.0.0` / CWE-605), inyecciones en parámetros de registro y manejo inseguro de excepciones al contactar al microservicio de notificaciones. | **Bloqueo en MEDIUM y HIGH:** En un Marketplace que maneja autenticación de clientes y órdenes de compra, no se pueden tolerar servicios escuchando en interfaces externas no controladas. | No se auditan advertencias de nivel LOW (como advertencias sobre importación de módulos estándar) porque no representan vectores de explotación directa en esta fase. |
| **3. Auditoría de IaC** | Trivy Config (v0.58) | Seguridad de Infraestructura como Código | Creación de buckets S3 con permisos públicos de lectura/escritura (fuga de órdenes) o bases de datos RDS con `publicly_accessible = true` accesibles desde cualquier IP pública de internet. | **Bloqueo estricto en HIGH y CRITICAL (exit-code 1):** La base de datos de usuarios y productos jamás debe ser alcanzable fuera de la VPC de la instancia EC2. | Se exceptuó la regla `AVD-AWS-0132` (cifrado obligatorio mediante CMK en AWS KMS) a través de `.trivyignore`, debido a que el rol educativo `LabRole` de AWS Academy carece de privilegios IAM para aprovisionar claves KMS personalizadas; se mitigó usando `AES256` nativo (SSE-S3). |
| **4. Inventario de Componentes** | Trivy / CycloneDX | Software Bill of Materials (SBOM) | Uso de dependencias obsoletas en `requirements.txt` (como versiones vulnerables de Flask, Requests o Gunicorn) susceptibles a ataques de cadena de suministro o denegación de servicio. | **Generación obligatoria de artefacto:** No bloquea la ejecución de forma directa en este paso, pero genera el inventario estandarizado `sbom_cyclonedx.json` para auditoría y trazabilidad regulatoria. | No se detiene el despliegue por dependencias transitivas sin parche disponible (*unfixable*), ya que requeriría reescribir frameworks base sin alternativa inmediata. |

---

## 2. Justificación de la Decisión Final Integrada

El pipeline implementa una compuerta de decisión única (`FALLOS_TOTALES -gt 0`) en lugar de escaneos aislados. Si cualquiera de las etapas de seguridad detecta una violación a las políticas de seguridad corporativas, el script finaliza con código de salida `exit 1` y marca el despliegue como `[BLOQUEADO]`, evitando que código o infraestructura vulnerables lleguen al entorno productivo.

## 3. Actualizacion Entrega Final: Mitigacion de CWE-306 y CWE-639 (BOLA)
- Etapa 2 ampliada: Se integro compuerta de verificacion de contratos de API para el endpoint de confirmaciones.
- Mitigacion CWE-306: Autenticacion obligatoria con token de sesion (HTTP 401 si falta credencial).
- Mitigacion CWE-639 (BOLA): Validacion de pertenencia pedido['usuario_id'] == usuario['id'] en PostgreSQL (HTTP 403 si es ajeno).
- Umbral: Bloqueo estricto Fail-Closed ante cualquier vulnerabilidad de autorizacion en codigo.
