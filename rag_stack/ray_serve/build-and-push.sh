#!/bin/bash
set -e

echo "================================================"
echo "  Building and Pushing Ray Serve Proxy"
echo "================================================"
echo ""

ECR_REPOSITORY="rag-rayserve"
IMAGE_TAG="${1:-latest}"
AWS_REGION="eu-west-2"

echo "Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "[OK] Account ID: ${AWS_ACCOUNT_ID}"
echo ""

FULL_IMAGE_NAME="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
FULL_IMAGE_NAME_LATEST="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"

echo "Image: ${FULL_IMAGE_NAME}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building Docker image..."
docker buildx build --platform linux/amd64 \
    -f Dockerfile \
    -t "${FULL_IMAGE_NAME}" \
    -t "${FULL_IMAGE_NAME_LATEST}" \
    --load .
echo "[OK] Image built"

echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
echo "[OK] Logged in to ECR"


echo "Pushing images to ECR..."
docker push "${FULL_IMAGE_NAME}"
if [ "$IMAGE_TAG" != "latest" ]; then
    docker push "${FULL_IMAGE_NAME_LATEST}"
fi
echo "[OK] Images pushed"

echo "================================================"
echo "  Build Complete"
echo "================================================"
echo ""
echo "Image: ${FULL_IMAGE_NAME}"
