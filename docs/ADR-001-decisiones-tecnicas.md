# ADR-001: Decisiones de Arquitectura Técnica y Seguridad

**Fecha:** 2026-09-15  
**Estado:** Aprobado  
**Contexto del Sistema:** Marketplace Seguro (Avance 2)

---

## 1. Contexto y Problema

Se requiere implementar una plataforma de comercio electrónico segura que permita el registro de usuarios, visualización de catálogo, gestión de carrito y checkout, garantizando desacoplamiento de servicios, cero credenciales quemadas, infraestructura cifrada y validación automatizada mediante un pipeline de seguridad.

---

## 2. Decisiones Técnicas Adoptadas

### Decisión 1: Framework Flask con Servidor WSGI Gunicorn
* **Elección:** Python 3 con Flask para endpoints REST y Gunicorn como servidor de producción.
* **Por qué se eligió:** Permite una arquitectura ligera, explícita y fácilmente auditable por herramientas SAST sin la sobrecarga ni la complejidad de configuración de frameworks monolíticos.
* **Alternativa descartada:** Servidor de desarrollo de Flask (`app.run`). Se descartó para el contenedor productivo porque es monohilo, vulnerable a ataques de agotamiento de recursos y expone trazas de depuración inseguras en caso de error.

### Decisión 2: Desacoplamiento del Microservicio de Notificaciones (Pieza Distintiva)
* **Elección:** Separar la lógica de confirmación de órdenes en un contenedor independiente (`marketplace_notificaciones`) consumido mediante HTTP POST interno.
* **Por qué se eligió:** Cumple con el requisito de modularidad. La caída del módulo de correos/notificaciones no interrumpe la navegación ni el agregado de productos al carrito en la API principal.
* **Alternativa descartada:** Implementar la función de notificación como una llamada síncrona dentro del mismo archivo `main.py` de la API. Se descartó porque violaría el requisito de contenerización independiente de la rúbrica.

### Decisión 3: Endurecimiento de Contenedores Docker (Hardening)
* **Elección:** Imagen base `python:3.11-slim`, ejecución bajo usuario no privilegiado (`USER appuser`) y directiva `HEALTHCHECK` activa.
* **Por qué se eligió:** Mitiga el riesgo de escalada de privilegios hacia el kernel de la instancia host en caso de una vulnerabilidad de ejecución remota de código en la aplicación web.
* **Alternativa descartada:** Imágenes base completas (`python:3.11`) o correr como `root`. Se descartó por inflar el peso de las imágenes y elevar drásticamente los hallazgos de CVEs en escaneos SCA.

### Decisión 4: Manejo de Infraestructura y Almacenamiento en AWS Academy
* **Elección:** S3 con cifrado SSE-S3 (AES-256) y bloqueo total de acceso público; RDS PostgreSQL en subred privada con cifrado en reposo habilitado.
* **Por qué se eligió:** Protege los datos personales de clientes y transacciones contra filtraciones accidentales a internet, operando estrictamente dentro de las limitaciones del rol `LabRole` del Learner Lab.
* **Alternativa descartada:** Base de datos relacional local en contenedor (`docker run postgres`). Se descartó porque la rúbrica exige infraestructura administrada real en la nube.
