# Cesar Tech

Cesar Eduardo Valdez Pinto · Al07003448 · LSCA2314 · Tema 3 Marketplace

Tienda de práctica con diseño azul buenardo, laptops, PC, RAM, SSD y componentes. Las compras no generan cargos ni envío de mercancía.

## Entrega final

El parche docente se probó en la instancia QA existente. El pipeline lo bloquea por falta de autenticación y autorización; la corrección pasa 37 pruebas y las etapas de secretos, SAST, IaC y SBOM. El original se conserva fuera del código ejecutable.

- [Clasificación](docs/clasificacion_hallazgo.md) y [respuesta al incidente](docs/respuesta_incidente.md)
- [Corrida bloqueada](reportes/pipeline_bloqueado.txt) y [corrida aprobada](reportes/pipeline_verde.txt)
- [Producción](docs/evidencia_produccion.md)
- [Correo real](docs/CORREO_REAL.md)
- [Declaración de IA](docs/declaracion_ia.md)

**Pendiente explícito:** comprobar correo real. El adaptador está implementado y probado con proveedores simulados, pero AWS Academy deniega SES y todavía falta un remitente SMTP autorizado. Un comprobante S3 no es evidencia de correo recibido.

## Ambientes

| Ambiente | Instancia | URL |
|---|---|---|
| QA del Avance 2 | `i-0d077a1e93b366368` | http://44.202.249.26:5000/ |
| Producción nueva | `i-02c5f6fbbbcae6fe0` | http://54.204.91.37:5000/ |

Cuenta `940828937790`, región `us-east-1`. Las IP pueden cambiar al reiniciar. Producción usa `marketplace_prod` y un bucket privado propio; QA conserva sus datos. Comparten el servidor RDS del laboratorio. No se modificó la cuenta del compañero.

## Operación

Copiar `.env.example` a `.env`, completar los datos privados de base, bucket, clave aleatoria de sesión y proveedor de correo; ejecutar `docker compose up -d --build`. API en 5000 y acuses en la red interna de Docker.

Ejecutar `bash pipeline/ejecutar_pipeline.sh` con Gitleaks, Bandit, Trivy, Docker y Python 3. Las pruebas unitarias no usan red. Los informes anteriores son históricos y describen el estado de aquel momento.
