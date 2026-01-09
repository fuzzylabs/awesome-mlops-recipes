#!/bin/bash
set -e

echo "================================================"
echo "  Deploying vLLM to Kubernetes"
echo "================================================"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
NAMESPACE="vllm"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl first."
    exit 1
fi

echo "[OK] kubectl found"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "[OK] Connected to Kubernetes cluster"
echo ""

# Create namespace if it doesn't exist
echo "Creating namespace..."
if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "[SKIP] Namespace '$NAMESPACE' already exists"
else
    kubectl create namespace "$NAMESPACE"
    echo "[OK] Namespace '$NAMESPACE' created"
fi
echo ""

# Apply StorageClass
echo "Applying StorageClass..."
kubectl apply -f storage-class-gp3.yaml
echo "[OK] StorageClass applied"
echo ""

# Apply PVC
echo "Applying PersistentVolumeClaim..."
kubectl apply -f pvc.yaml
echo "[OK] PVC applied"
echo ""

# Wait for PVC to be created
echo "Waiting for PVC to be created..."
kubectl wait --for=create pvc/qwen3 -n "$NAMESPACE" --timeout=30s 2>/dev/null || true
echo "[OK] PVC created (will bind when pod starts)"
echo ""

# Apply Deployment
echo "Applying Deployment..."
kubectl apply -f deployment.yaml
echo "[OK] Deployment applied"
echo ""

# Apply Service
echo "Applying Service..."
kubectl apply -f service.yaml
echo "[OK] Service applied"
echo ""
