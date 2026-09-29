#!/usr/bin/env bash

echo "========================================================"
echo "    AUDITORIA AUTOMATICA DE ENTREGA - AVANCE 2"
echo "========================================================"

ERRORES=0

revisar_archivo() {
    local ruta="$1"
    local desc="$2"
    if [ ! -s "$ruta" ]; then
        echo "  [FALTA] $desc -> $ruta (No existe o esta vacio)"
        ERRORES=$((ERRORES + 1))
    else
        echo "  [OK] $desc -> $ruta"
    fi
}

revisar_campo_incompleto() {
    local ruta="$1"
    if [ -f "$ruta" ] && grep -qE "\[COMPLETAR\]|TODO|REEMPLAZAR" "$ruta"; then
        echo "  [ALERTA] $ruta contiene texto de plantilla sin completar."
        ERRORES=$((ERRORES + 1))
    fi
}

echo "1. Validando archivos de aplicacion y contenedores..."
revisar_archivo "app/main.py" "API Principal"
revisar_archivo "app/requirements.txt" "Dependencias API"
revisar_archivo "notificaciones/main.py" "Microservicio Notificaciones"
revisar_archivo "notificaciones/requirements.txt" "Dependencias Notificaciones"
revisar_archivo "Dockerfile" "Dockerfile API"
revisar_archivo "Dockerfile.notif" "Dockerfile Notificaciones"
revisar_archivo "docker-compose.yml" "Orquestacion Docker Compose"

echo "2. Validando Infraestructura como Codigo..."
revisar_archivo "infra/main.tf" "Definicion Terraform"

echo "3. Validando Pipeline y Reportes requeridos..."
revisar_archivo "pipeline/ejecutar_pipeline.sh" "Script de Pipeline"
revisar_archivo "reportes/corrida_roja.txt" "Evidencia Corrida Roja"
revisar_archivo "reportes/corrida_verde.txt" "Evidencia Corrida Verde"
revisar_archivo "reportes/sbom_cyclonedx.json" "Inventario SBOM"

echo "4. Validando Documentacion obligatoria..."
revisar_archivo "docs/README.md" "Guia README"
revisar_archivo "docs/ADR-001-decisiones-tecnicas.md" "Registro ADR"
revisar_archivo "docs/tabla_decisiones_pipeline.md" "Tabla de Decisiones"
revisar_archivo "docs/declaracion_uso_ia.md" "Declaracion de IA"

echo "5. Comprobando ausencia de plantillas sin rellenar..."
for doc in docs/*.md; do
    revisar_campo_incompleto "$doc"
done

echo "--------------------------------------------------------"
if [ $ERRORES -eq 0 ]; then
    echo "ESTADO DE ENTREGA: [COMPLETO Y AUDITADO CON EXITO]"
    echo "Todos los artefactos requeridos estan presentes y no vacios."
else
    echo "ESTADO DE ENTREGA: [PENDIENTES DETECTADOS: $ERRORES]"
    exit 1
fi
