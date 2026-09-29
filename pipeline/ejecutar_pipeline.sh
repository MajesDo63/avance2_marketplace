#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPORT_DIR="${QA_REPORT_DIR:-reportes/qa_20260929}"
mkdir -p "$REPORT_DIR"
FAILURES=0
printf 'PIPELINE QA CESAR | %s\n' "$(date -u +%FT%TZ)"
printf 'Bloqueo: errores de herramientas, secretos, SAST >= MEDIUM, IaC HIGH/CRITICAL, pruebas o SBOM inválido.\n'
for tool in gitleaks trivy docker python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then echo "BLOQUEADO: herramienta ausente: $tool"; exit 1; fi
done
BANDIT_CMD="$(command -v bandit || true)"
if [ -z "$BANDIT_CMD" ] && [ -x "$HOME/.local/bin/bandit" ]; then BANDIT_CMD="$HOME/.local/bin/bandit"; fi
if [ -z "$BANDIT_CMD" ]; then echo 'BLOQUEADO: Bandit no está disponible'; exit 1; fi
echo '[1/5] Secretos'
if [ -d .git ] && git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo 'BLOQUEADO: el archivo privado .env está versionado'; exit 1
fi
if gitleaks detect --no-git --source . --config .gitleaks.toml --redact --exit-code 1 > "$REPORT_DIR/gitleaks.txt" 2>&1; then
  echo 'PASS: secretos'
else echo 'FAIL: secretos o error del escáner'; FAILURES=$((FAILURES+1)); fi
echo '[2/5] SAST'
if "$BANDIT_CMD" -r app/ notificaciones/ -ll > "$REPORT_DIR/bandit.txt" 2>&1; then
  echo 'PASS: SAST'
else echo 'FAIL: SAST'; cat "$REPORT_DIR/bandit.txt"; FAILURES=$((FAILURES+1)); fi
echo '[3/5] Pruebas funcionales y autorización'
if python3 pipeline/auditar_parche.py > "$REPORT_DIR/pruebas.txt" 2>&1; then
  echo 'PASS: pruebas de comportamiento'
else echo 'FAIL: pruebas de comportamiento'; FAILURES=$((FAILURES+1)); fi
cat "$REPORT_DIR/pruebas.txt"
echo '[4/5] IaC (análisis, sin aplicar Terraform)'
if trivy config --severity HIGH,CRITICAL --exit-code 1 infra/ > "$REPORT_DIR/trivy_iac.txt" 2>&1; then
  echo 'PASS: IaC'
else echo 'FAIL: IaC'; cat "$REPORT_DIR/trivy_iac.txt"; FAILURES=$((FAILURES+1)); fi
echo '[5/5] SBOM nuevo'
SBOM="$REPORT_DIR/sbom_cyclonedx.json"
TEMP_SBOM="$REPORT_DIR/sbom_nuevo.json"
if trivy fs --format cyclonedx --output "$TEMP_SBOM" app/ > "$REPORT_DIR/sbom_log.txt" 2>&1 && python3 - "$TEMP_SBOM" <<'PY'
import json,sys
with open(sys.argv[1]) as f:
    data=json.load(f)
assert data.get('bomFormat')=='CycloneDX' and data.get('components'), 'SBOM vacío o inválido'
print('PASS: SBOM CycloneDX válido, componentes:',len(data['components']))
PY
then mv "$TEMP_SBOM" "$SBOM"
else echo 'FAIL: generación/validación de SBOM'; FAILURES=$((FAILURES+1)); fi
if [ "$FAILURES" -ne 0 ]; then
  echo "VEREDICTO: BLOQUEADO | Etapas fallidas: $FAILURES"; exit 1
fi
echo 'VEREDICTO: PERMITIDO para validación y despliegue en QA. No acredita promoción a Producción.'
