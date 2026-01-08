#!/bin/bash
set -e

echo "================================================"
echo "  Deploying Locust"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="locust"

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

echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

echo "Applying Deployment..."
kubectl apply -f deployment.yaml

echo "Applying Service..."
kubectl apply -f service.yaml

echo "[OK] Locust deployed"
