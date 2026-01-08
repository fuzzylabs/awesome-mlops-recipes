#!/bin/bash
set -e

echo "================================================"
echo "  Deploying Metaflow Service to Kubernetes"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="metaflow"

if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl first."
    exit 1
fi

echo "[OK] kubectl found"

if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "[OK] Connected to Kubernetes cluster"
echo ""

echo "Creating namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "[SKIP] Namespace '$NAMESPACE' already exists"
else
    kubectl create namespace "$NAMESPACE"
    echo "[OK] Namespace '$NAMESPACE' created"
fi
echo ""

if [ ! -f secret.yaml ]; then
    echo "Error: secret.yaml not found!"
    echo ""
    echo "Please create secret.yaml from the example:"
    echo "  1. cp secret.yaml.example secret.yaml"
    echo "  2. Edit secret.yaml and add your actual credentials"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi

echo "Applying ServiceAccount..."
kubectl apply -f serviceaccount.yaml
echo "[OK] ServiceAccount applied"
echo ""

echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml
echo "[OK] ConfigMap applied"
echo ""

echo "Applying Secret..."
kubectl apply -f secret.yaml
echo "[OK] Secret applied"
echo ""

echo "Applying Deployment..."
kubectl apply -f deployment.yaml
echo "[OK] Deployment applied"
echo ""

echo "Applying Service..."
kubectl apply -f service.yaml
echo "[OK] Service applied"
echo ""

echo "================================================"
echo "  Next Steps"
echo "================================================"
echo ""
echo "Wait for the pod to be ready:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "Port-forward to test locally:"
echo "  kubectl port-forward -n $NAMESPACE svc/metaflow 8080:8080"
echo ""
echo "[OK] Deployment complete"
