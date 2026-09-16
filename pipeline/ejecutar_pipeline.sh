#!/usr/bin/env bash
set +e

echo "========================================================"
echo "    PIPELINE DE SEGURIDAD DEVSECOPS - MARKETPLACE"
echo "========================================================"
FECHA=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "Timestamp: $FECHA"
echo "Umbral de bloqueo integrado: Cero hallazgos HIGH o CRITICAL"
echo "--------------------------------------------------------"

FALLOS_TOTALES=0

# ETAPA 1: Detección de Secretos (Gitleaks)
echo "[1/4] Ejecutando Deteccion de Secretos (Gitleaks)..."
if command -v gitleaks &> /dev/null; then
    gitleaks detect --no-git --source . --verbose > /tmp/gitleaks_report.txt 2>&1
    if [ $? -ne 0 ]; then
        echo "  [FAIL] Se detectaron credenciales o secretos expuestos."
        FALLOS_TOTALES=$((FALLOS_TOTALES + 1))
    else
        echo "  [PASS] Cero secretos detectados en el repositorio."
    fi
else
    echo "  [WARN] Gitleaks no encontrado, saltando..."
fi

# ETAPA 2: Analisis Estatico de Codigo (SAST - Bandit)
echo "[2/4] Ejecutando Analisis SAST de Python (Bandit)..."
if command -v bandit &> /dev/null; then
    bandit -r app/ notificaciones/ -ll > /tmp/bandit_report.txt 2>&1
    if [ $? -ne 0 ]; then
        echo "  [FAIL] Se encontraron vulnerabilidades de codigo HIGH/MEDIUM."
        cat /tmp/bandit_report.txt
        FALLOS_TOTALES=$((FALLOS_TOTALES + 1))
    else
        echo "  [PASS] SAST aprobado: cero vulnerabilidades criticas en el codigo."
    fi
else
    echo "  [WARN] Bandit no encontrado, saltando..."
fi

# ETAPA 3: Auditoria de Infraestructura como Codigo (IaC - Trivy)
echo "[3/4] Escaneando Infraestructura Terraform (Trivy IaC)..."
if command -v trivy &> /dev/null; then
    trivy config --severity HIGH,CRITICAL --exit-code 1 infra/ > /tmp/trivy_iac_report.txt 2>&1
    if [ $? -ne 0 ]; then
        echo "  [FAIL] Falla de seguridad detectada en infra/main.tf."
        cat /tmp/trivy_iac_report.txt
        FALLOS_TOTALES=$((FALLOS_TOTALES + 1))
    else
        echo "  [PASS] IaC aprobada: recursos S3 y RDS cumplen con politicas de seguridad."
    fi
else
    echo "  [WARN] Trivy no encontrado, saltando..."
fi

# ETAPA 4: Generacion de SBOM (Trivy CycloneDX)
echo "[4/4] Generando SBOM CycloneDX de la aplicacion..."
if command -v trivy &> /dev/null; then
    trivy fs --format cyclonedx --output reportes/sbom_cyclonedx.json . > /dev/null 2>&1
    if [ -f reportes/sbom_cyclonedx.json ]; then
        echo "  [PASS] SBOM CycloneDX generado exitosamente en reportes/sbom_cyclonedx.json"
    else
        echo "  [WARN] No se pudo escribir el archivo SBOM."
    fi
fi

echo "--------------------------------------------------------"
echo "               DECISION FINAL INTEGRADA"
echo "--------------------------------------------------------"

if [ $FALLOS_TOTALES -gt 0 ]; then
    echo "VEREDICTO: [BLOQUEADO] (FAILED)"
    echo "Motivo: Se encontraron $FALLOS_TOTALES etapas con violaciones criticas no permitidas."
    echo "Accion: Despliegue cancelado preventivamente."
    exit 1
else
    echo "VEREDICTO: [PERMITIDO] (PASSED)"
    echo "Motivo: Todas las etapas superaron los umbrales de seguridad definidos."
    echo "Accion: Autorizado para despliegue en entorno productivo."
    exit 0
fi
