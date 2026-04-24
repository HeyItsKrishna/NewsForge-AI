#!/bin/bash
set -e
PROJECT_ID="newsforge-ai-491805"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="newsforge-ai"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
GOOGLE_API_KEY="${GOOGLE_API_KEY:?Please export GOOGLE_API_KEY}"
NEWS_API_KEY="${NEWS_API_KEY:?Please export NEWS_API_KEY}"
echo "Enabling APIs..."
gcloud services enable run.googleapis.com containerregistry.googleapis.com --project="${PROJECT_ID}" --quiet
echo "Building image..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}" .
echo "Deploying..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 300 \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY},NEWS_API_KEY=${NEWS_API_KEY},MODEL=gemini-2.0-flash" \
  --project="${PROJECT_ID}" \
  --quiet
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --project="${PROJECT_ID}" --format="value(status.url)")
echo "DEPLOYED: ${SERVICE_URL}"
