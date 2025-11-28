#!/bin/bash
set -e

echo "Installing MLflow Helm Chart on Kubernetes..."

MLFLOW_S3_BUCKET="self-hosted-agent-mlflow-artifacts-a29dbbb"
MLFLOW_S3_ROLE_ARN="arn:aws:iam::196980041487:role/self-hosted-agent-mlflow-s3-role-35785a0"
MLFLOW_DB_ENDPOINT="self-hosted-agent-mlflow-db.cjoke00gu0ym.eu-west-2.rds.amazonaws.com"
MLFLOW_DB_NAME="mlflow"
MLFLOW_DB_USERNAME="mlflow"
MLFLOW_DB_PASSWORD="password123"

# Add Helm repository
echo "Adding Helm repository..."
helm repo add community-charts https://community-charts.github.io/helm-charts
helm repo update

# Install/upgrade MLflow
echo "Installing MLflow..."
helm upgrade --install mlflow \
  community-charts/mlflow \
  --version 1.8.0 \
  --namespace mlflow \
  --create-namespace \
  --set backendStore.postgres.enabled=true \
  --set backendStore.postgres.host="$MLFLOW_DB_ENDPOINT" \
  --set backendStore.postgres.port=5432 \
  --set backendStore.postgres.database="$MLFLOW_DB_NAME" \
  --set backendStore.postgres.user="$MLFLOW_DB_USERNAME" \
  --set backendStore.postgres.password="$MLFLOW_DB_PASSWORD" \
  --set artifactRoot.s3.enabled=true \
  --set artifactRoot.s3.bucket="$MLFLOW_S3_BUCKET" \
  --set serviceAccount.create=true \
  --set serviceAccount.name=mlflow \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="$MLFLOW_S3_ROLE_ARN" \
  --set service.type=ClusterIP \
  --set service.port=5000 \
  --set extraEnvVars.MLFLOW_HOST="0.0.0.0" \
  --set extraEnvVars.MLFLOW_SERVER_ALLOWED_HOSTS="mlflow.mlflow.svc.cluster.local:5000" \
  --set extraEnvVars.MLFLOW_GUNICORN_OPTS="--timeout 180" \
  # The above extraEnvVars stuff are needed to allow mlflow to be accessed from the agent since mlflow version 3.5.0
  # https://github.com/mlflow/mlflow/issues/16659
  # You might want to take a more secure approach in production

echo ""
echo "MLflow installed successfully!"
echo ""
