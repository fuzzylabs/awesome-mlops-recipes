#!/bin/bash
set -e

echo "================================================"
echo "  Deploying Ray Serve (vLLM proxy)"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="rayserve"

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

echo "Creating namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "[SKIP] Namespace '$NAMESPACE' already exists"
else
    kubectl create namespace "$NAMESPACE"
    echo "[OK] Namespace '$NAMESPACE' created"
fi

echo "Applying RayService..."
kubectl apply -f rayservice.yaml

echo "[OK] RayService applied"
