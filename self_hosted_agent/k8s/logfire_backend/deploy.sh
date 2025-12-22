#!/bin/bash
set -e

echo "================================================"
echo "  Deploying Logfire backend to Kubernetes"
echo "================================================"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
NAMESPACE="logfire"

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
