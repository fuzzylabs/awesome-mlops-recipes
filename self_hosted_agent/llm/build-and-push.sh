#!/bin/bash
set -e

# Configuration
ECR_REPO_NAME="self-hosted-agent"
IMAGE_TAG="${1:-latest}"  # Use first argument or default to 'latest'
REGION="eu-west-2"  # Change if needed

echo "🔧 Building and pushing Docker image to ECR..."
echo "📦 Repository: ${ECR_REPO_NAME}"
echo "🏷️  Tag: ${IMAGE_TAG}"
echo "🌍 Region: ${REGION}"
echo ""

# Get AWS account ID
echo "🔍 Getting AWS account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ Account ID: ${ACCOUNT_ID}"
echo ""

# ECR repository URL
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
FULL_IMAGE_NAME="${ECR_URL}/${ECR_REPO_NAME}:${IMAGE_TAG}"

# Login to ECRxw
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_URL}
echo "✅ Logged in successfully"
echo ""

# Build the image for AMD64 platform (EKS nodes)
echo "🏗️  Building Docker image for linux/amd64..."
docker buildx build --platform linux/amd64 -t ${ECR_REPO_NAME}:${IMAGE_TAG} --load .
echo "✅ Build complete"
echo ""

# Tag the image for ECR
echo "🏷️  Tagging image for ECR..."
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}
echo "✅ Tagged as ${FULL_IMAGE_NAME}"
echo ""

# Push to ECR
echo "⬆️  Pushing to ECR..."
docker push ${FULL_IMAGE_NAME}
echo "✅ Push complete"
echo ""

echo "🎉 Done! Image available at:"
echo "   ${FULL_IMAGE_NAME}"
echo ""
echo "📝 To use in Kubernetes, update your deployment with:"
echo "   image: ${FULL_IMAGE_NAME}"

