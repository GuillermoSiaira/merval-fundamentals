#!/usr/bin/env bash
# deploy.sh
# Deploy de la Cloud Function a GCP
# Uso: cd gcp && bash deploy.sh
# Requiere: gcloud CLI instalado y autenticado

set -euo pipefail

# ---- Config ----
PROJECT_ID="${GCP_PROJECT_ID:-merval-fundamentals}"
FUNCTION_NAME="merval-analysis"
REGION="southamerica-east1"
RUNTIME="python311"

# Verificar que las variables de entorno necesarias estén definidas
: "${ALPHACAST_API_KEY:?ERROR: ALPHACAST_API_KEY no está definida}"
: "${TELEGRAM_BOT_TOKEN:?ERROR: TELEGRAM_BOT_TOKEN no está definida}"
: "${TELEGRAM_CHAT_ID:?ERROR: TELEGRAM_CHAT_ID no está definida}"

echo "🚀 Deploying $FUNCTION_NAME a GCP..."
echo "   Proyecto: $PROJECT_ID"
echo "   Región: $REGION"
echo "   Runtime: $RUNTIME"

# Ir a la raíz del repo (el padre de gcp/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

gcloud functions deploy "$FUNCTION_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --runtime="$RUNTIME" \
  --trigger-http \
  --allow-unauthenticated \
  --source="." \
  --entry-point="merval_analysis" \
  --memory="512MB" \
  --timeout="300s" \
  --set-env-vars="ALPHACAST_API_KEY=${ALPHACAST_API_KEY}" \
  --set-env-vars="TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}" \
  --set-env-vars="TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}" \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}"

echo ""
echo "✅ Deploy completo!"
echo ""
echo "URL de la función:"
gcloud functions describe "$FUNCTION_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="value(httpsTrigger.url)"
