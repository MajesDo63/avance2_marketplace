# Declaración Obligatoria sobre el Uso de Inteligencia Artificial

**Estudiante:** César Eduardo Valdez Pinto  
**Curso:** LSCA2314 - Herramientas de Tecnologías de Información  
**Periodo:** AD26  
**Proyecto:** El Reto - Entrega Final: De QA a Producción (Marketplace)

---

## 1. Herramientas de IA Utilizadas
* **Modelo / Asistente:** Asistente de IA generativa colaborativo.
* **Propósito:** Generación de la plantilla visual del frontend ("César Tech Store"), soporte en el diseño de aserciones para pruebas unitarias de autorización y asistencia en la propuesta del parche de remediación para la API.

---

## 2. Componentes Asistidos por IA
* **Interfaz de Usuario (Frontend):** Maquetación de la interfaz web responsiva en HTML/CSS para el catálogo, vista de pedidos y tienda virtual de "César Tech Store".
* **Borrador de Remediación (app/reenviar_confirmacion.py):** Sugerencia del esqueleto lógico para invocar la función de autenticación y verificar la igualdad entre el propietario del pedido y el usuario de la sesión.
* **Automatización de Casos de Prueba:** Estructuración de pruebas unitarias (test_qa.py) con simulación (mocking) de los métodos de correo para validar códigos de respuesta HTTP (401, 403, 503). 

---

## 3. Auditoría, Pruebas y Correcciones Realizadas por el Alumno
* **Validación de Lógica de Negocio y Control de Acceso:** La IA propuso inicialmente un bloqueo genérico; yo analicé el impacto real clasificando la severidad en base a CWE-306 (Falta de Autenticación) y CWE-639 / BOLA (Falta de Autorización a Nivel de Objeto), asegurando que el endpoint devolviera estrictamente 401 Unauthorized para peticiones anónimas y 403 Forbidden para accesos a pedidos ajenos.
* **Ajuste de Manejo de Excepciones en el Worker:** Se corrigió el manejo de errores en el reenvío de notificaciones; se implementó el bloque try/except para atrapar fallos del servicio de mensajería y retornar un código 503 Service Unavailable controlado, evitando fugas de información o caídas en la conexión con la base de datos PostgreSQL en RDS.
* **Gestión de Falsos Positivos en Gitleaks:** Se auditó una detección de secretos sobre un valor dummy de SECRET_KEY, remediándolo mediante variables de entorno en blanco en la configuración local sin desactivar la regla del escáner en el pipeline.
* **Aprovisionamiento y Despliegue Real en AWS:** Creación, configuración de Security Groups (puerto 5000) y verificación manual de la nueva instancia EC2 de Producción (i-02c5f6fbbbcae6fe0), asegurando el direccionamiento público (54.204.91.37) y la sincronización con la instancia previa de QA (i-0d077a1e93b366368).
* **Ejecución y Verificación de la Compuerta Fail-Closed:** Comprobación directa en consola del bloqueo del pipeline ante el código docente y posterior validación de la aprobación de las 37 pruebas funcionales y de regresión previo a la promoción de código.

* 
