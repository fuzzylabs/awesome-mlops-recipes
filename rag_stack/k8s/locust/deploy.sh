#!/bin/bash
set -e

echo "================================================"
echo "  Deploying Locust"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="locust"
LOCUSTFILE_PATH="${SCRIPT_DIR}/../../load_testing/locustfile.py"

if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl first."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "Creating namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "[SKIP] Namespace '$NAMESPACE' already exists"
else
    kubectl create namespace "$NAMESPACE"
    echo "[OK] Namespace '$NAMESPACE' created"
fi

echo "Syncing ConfigMap..."
if [ ! -f "$LOCUSTFILE_PATH" ]; then
    echo "Error: locustfile not found at ${LOCUSTFILE_PATH}"
    exit 1
fi

kubectl create configmap locustfile \
    --from-file=locustfile.py="$LOCUSTFILE_PATH" \
    -n "$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "Applying Deployment..."
kubectl apply -f deployment.yaml

echo "Applying Service..."
kubectl apply -f service.yaml

echo "[OK] Locust deployed"
