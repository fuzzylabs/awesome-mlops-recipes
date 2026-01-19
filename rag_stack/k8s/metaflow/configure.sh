#!/bin/bash
set -e

# Configure Metaflow Kubernetes manifests from environment variables.
#
# Required environment variables (from Pulumi outputs):
#   METAFLOW_S3_BUCKET       - S3 bucket for Metaflow data (e.g., mlflowS3Bucket)
#   METAFLOW_RDS_ENDPOINT    - RDS endpoint without port (e.g., mlflowDbEndpoint)
#   METAFLOW_DB_PASSWORD     - Database password (e.g., mlflowDbPassword)
#   METAFLOW_S3_ROLE_ARN     - IRSA role ARN for S3 access (e.g., metaflowS3RoleArn)
#   RAG_METAFLOW_ECR_URL     - ECR URL for the Metaflow image (e.g., ragMetaflowEcrUrl)
#
# Usage:
#   # Set variables manually
#   export METAFLOW_S3_BUCKET=my-bucket
#   export METAFLOW_RDS_ENDPOINT=my-db.xxx.rds.amazonaws.com
#   export METAFLOW_DB_PASSWORD=mypassword
#   export METAFLOW_S3_ROLE_ARN=arn:aws:iam::123456789012:role/metaflow-s3-role
#   export RAG_METAFLOW_ECR_URL=123456789012.dkr.ecr.eu-west-1.amazonaws.com/rag-metaflow
#   ./configure.sh
#
#   # Or source from Pulumi
#   cd /path/to/awesome-mlops-recipes-iac/rag_stack/pulumi
#   export METAFLOW_S3_BUCKET=$(pulumi stack output mlflowS3Bucket)
#   export METAFLOW_RDS_ENDPOINT=$(pulumi stack output mlflowDbEndpoint)
#   export METAFLOW_DB_PASSWORD=$(pulumi config get mlflowDbPassword)
#   export METAFLOW_S3_ROLE_ARN=$(pulumi stack output metaflowS3RoleArn)
#   export RAG_METAFLOW_ECR_URL=$(pulumi stack output ragMetaflowEcrUrl)
#   cd /path/to/awesome-mlops-recipes/rag_stack/k8s/metaflow
#   ./configure.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================"
echo "  Configuring Metaflow Kubernetes Manifests"
echo "================================================"
echo ""

# Check required environment variables
MISSING_VARS=()

[ -z "$METAFLOW_S3_BUCKET" ] && MISSING_VARS+=("METAFLOW_S3_BUCKET")
[ -z "$METAFLOW_RDS_ENDPOINT" ] && MISSING_VARS+=("METAFLOW_RDS_ENDPOINT")
[ -z "$METAFLOW_DB_PASSWORD" ] && MISSING_VARS+=("METAFLOW_DB_PASSWORD")
[ -z "$METAFLOW_S3_ROLE_ARN" ] && MISSING_VARS+=("METAFLOW_S3_ROLE_ARN")
[ -z "$RAG_METAFLOW_ECR_URL" ] && MISSING_VARS+=("RAG_METAFLOW_ECR_URL")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "Error: Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Set these from Pulumi outputs:"
    echo "  cd /path/to/awesome-mlops-recipes-iac/rag_stack/pulumi"
    echo "  export METAFLOW_S3_BUCKET=\$(pulumi stack output mlflowS3Bucket)"
    echo "  export METAFLOW_RDS_ENDPOINT=\$(pulumi stack output mlflowDbEndpoint)"
    echo "  export METAFLOW_DB_PASSWORD=\$(pulumi config get mlflowDbPassword)"
    echo "  export METAFLOW_S3_ROLE_ARN=\$(pulumi stack output metaflowS3RoleArn)"
    echo "  export RAG_METAFLOW_ECR_URL=\$(pulumi stack output ragMetaflowEcrUrl)"
    exit 1
fi

echo "Using configuration:"
echo "  S3 Bucket:     $METAFLOW_S3_BUCKET"
echo "  RDS Endpoint:  $METAFLOW_RDS_ENDPOINT"
echo "  S3 Role ARN:   $METAFLOW_S3_ROLE_ARN"
echo "  ECR URL:       $RAG_METAFLOW_ECR_URL"
echo ""

# Update configmap.yaml
echo "Updating configmap.yaml..."
sed -i.bak \
    -e "s|s3://your-bucket/metaflow|s3://${METAFLOW_S3_BUCKET}/metaflow|g" \
    -e "s|your-rds-endpoint|${METAFLOW_RDS_ENDPOINT}|g" \
    configmap.yaml
rm -f configmap.yaml.bak
echo "[OK] configmap.yaml updated"

# Update serviceaccount.yaml
echo "Updating serviceaccount.yaml..."
sed -i.bak \
    -e "s|arn:aws:iam::123456789012:role/metaflow-s3-role|${METAFLOW_S3_ROLE_ARN}|g" \
    serviceaccount.yaml
rm -f serviceaccount.yaml.bak
echo "[OK] serviceaccount.yaml updated"

# Update deployment.yaml
echo "Updating deployment.yaml..."
sed -i.bak \
    -e "s|REPLACE_WITH_RAG_METAFLOW_ECR_URL|${RAG_METAFLOW_ECR_URL}|g" \
    deployment.yaml
rm -f deployment.yaml.bak
echo "[OK] deployment.yaml updated"

# Create secret.yaml from example
echo "Creating secret.yaml..."
sed "s|your-password|${METAFLOW_DB_PASSWORD}|g" secret.yaml.example > secret.yaml
echo "[OK] secret.yaml created"

echo ""
echo "================================================"
echo "  Configuration Complete"
echo "================================================"
echo ""
echo "Next step: deploy with ./deploy.sh"
