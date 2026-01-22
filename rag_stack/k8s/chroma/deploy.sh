#!/bin/bash
set -e

echo "================================================"
echo "  Deploying Chroma to Kubernetes"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="chroma"

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

echo "Applying StorageClass..."
kubectl apply -f storage-class-gp3.yaml
echo "[OK] StorageClass applied"
echo ""

echo "Applying PersistentVolumeClaim..."
kubectl apply -f pvc.yaml
echo "[OK] PVC applied"
echo ""

echo "Applying Deployment..."
kubectl apply -f deployment.yaml
echo "[OK] Deployment applied"
echo ""

echo "Applying Service..."
kubectl apply -f service.yaml
echo "[OK] Service applied"
echo ""
