#!/usr/bin/env bash
set -euo pipefail

BUCKET_NAME="todosphere-attachments"
REGION="us-east-1"

echo "LocalStack init: creating S3 bucket ${BUCKET_NAME}..."

awslocal s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"

awslocal s3api put-bucket-cors \
  --bucket "${BUCKET_NAME}" \
  --cors-configuration '{
    "CORSRules": [
      {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
      }
    ]
  }'

echo "LocalStack init: bucket ${BUCKET_NAME} created and CORS configured."
