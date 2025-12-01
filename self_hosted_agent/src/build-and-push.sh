#!/bin/bash
set -e

echo "================================================"
echo "  Building and Pushing PR Review Agent"
echo "================================================"
echo ""

# Configuration
ECR_REPOSITORY="agent-server"
IMAGE_TAG="${1:-latest}"  # Use first argument or default to 'latest'
AWS_REGION="eu-west-2"  # Change if needed

# Get AWS account ID
echo "Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "[OK] Account ID: ${AWS_ACCOUNT_ID}"
echo ""

FULL_IMAGE_NAME="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
FULL_IMAGE_NAME_LATEST="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"

echo "Image: $FULL_IMAGE_NAME"
echo ""

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Build Docker image
echo "Building Docker image..."
docker buildx build --platform linux/amd64 \
    -f src/Dockerfile \
    -t "${FULL_IMAGE_NAME}" \
    -t "${FULL_IMAGE_NAME_LATEST}" \
    --load .
echo "[OK] Image built"
echo ""

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
echo "[OK] Logged in to ECR"
echo ""

# Push images
echo "Pushing images to ECR..."
docker push "${FULL_IMAGE_NAME}"
if [ "$IMAGE_TAG" != "latest" ]; then
    docker push "${FULL_IMAGE_NAME_LATEST}"
fi
echo "[OK] Images pushed"
echo ""

echo "================================================"
echo "  Build Complete"
echo "================================================"
echo ""
echo "Image: ${FULL_IMAGE_NAME}"
echo ""
