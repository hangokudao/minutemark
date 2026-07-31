#!/bin/sh
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
  echo "사용법: ./cloudrun-deploy.sh PROJECT_ID [SERVICE_NAME] [REGION]" >&2
  exit 2
fi

PROJECT_ID=$1
SERVICE_NAME=${2:-minutemark}
REGION=${3:-asia-northeast3}
SECRET_NAME=minutemark-a6-api-key
DEPLOY_COMMIT=$(git rev-parse HEAD 2>/dev/null || printf manual)

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1)
if [ -z "$ACCOUNT" ]; then
  echo "활성 Google Cloud 계정이 없습니다. 먼저 gcloud auth login을 실행하세요." >&2
  exit 2
fi

if ! gcloud secrets describe "$SECRET_NAME" \
  --project "$PROJECT_ID" >/dev/null 2>&1; then
  echo "Secret Manager에 $SECRET_NAME 비밀이 없습니다." >&2
  echo "NOTES.md의 'Cloud Run 최초 설정' 명령을 먼저 실행하세요." >&2
  exit 2
fi

echo "계정: $ACCOUNT"
echo "프로젝트: $PROJECT_ID"
echo "서비스: $SERVICE_NAME ($REGION)"

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 4Gi \
  --concurrency 1 \
  --min 0 \
  --max 1 \
  --timeout 180 \
  --set-env-vars "APP_COMMIT_SHA=${DEPLOY_COMMIT},A6_API_BASE=https://api.a6api.com/v1,A6_MODEL=claude-sonnet-5,A6_VENDOR_ID=1263,A6_INPUT_USD_PER_M=0.0180,A6_OUTPUT_USD_PER_M=0.0900,A6_RUN_BUDGET_USD=1.0,A6_REQUEST_RESERVE_USD=0.01,A6_REQUEST_TIMEOUT_SECONDS=60,WHISPER_LANGUAGE=auto,MAX_AUDIO_DURATION_SECONDS=120,MAX_ANALYSES_PER_INSTANCE=50,BUDGET_PERSISTENCE=ephemeral" \
  --set-secrets "A6_API_KEY=${SECRET_NAME}:latest"
