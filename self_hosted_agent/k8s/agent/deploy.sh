#!/bin/bash
set -e

echo "================================================"
echo "  Deploying PR Review Agent to Kubernetes"
echo "================================================"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
NAMESPACE="agent"

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

# Check if secret.yaml exists
if [ ! -f secret.yaml ]; then
    echo "Error: secret.yaml not found!"
    echo ""
    echo "Please create secret.yaml from the example:"
    echo "  1. cp secret.yaml.example secret.yaml"
    echo "  2. Edit secret.yaml and add your actual tokens"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi

# Apply Secret
echo "Applying Secret..."
kubectl apply -f secret.yaml
echo "[OK] Secret applied"
echo ""

# Apply ConfigMap
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml
echo "[OK] ConfigMap applied"
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

echo "================================================"
echo "  Deployment Status"
echo "================================================"
echo ""

echo "Namespace:"
kubectl get namespace "$NAMESPACE"
echo ""

echo "Deployment:"
kubectl get deployment -n "$NAMESPACE"
echo ""

echo "Pods:"
kubectl get pods -n "$NAMESPACE"
echo ""

echo "Service:"
kubectl get svc -n "$NAMESPACE"
echo ""

echo "================================================"
echo "  Next Steps"
echo "================================================"
echo ""
echo "Watch pod status:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "View logs:"
echo "  kubectl logs -n $NAMESPACE -l app=pr-review-agent -f"
echo ""
echo "Describe pod (for troubleshooting):"
echo "  kubectl describe pod -n $NAMESPACE -l app=pr-review-agent"
echo ""
echo "Port-forward to test locally:"
echo "  kubectl port-forward -n $NAMESPACE svc/pr-review-agent 8080:8080"
echo ""
echo "Test the API:"
echo "  curl http://localhost:8080/health"
echo "  curl -X POST http://localhost:8080/review -H 'Content-Type: application/json' -d '{\"pr_title\":\"Add new feature\"}'"
echo ""
echo "To delete everything:"
echo "  ./teardown.sh"
echo ""
echo "[OK] Deployment complete"

