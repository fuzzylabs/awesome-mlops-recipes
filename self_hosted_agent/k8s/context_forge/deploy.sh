#!/bin/bash
set -e

echo "================================================"
echo "  Deploying ContextForge to Kubernetes"
echo "================================================"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
NAMESPACE="context-forge"
PLUGIN_CONFIG_PATH="$SCRIPT_DIR/../../context_forge/plugins/config.yaml"

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
    echo "  2. Edit secret.yaml and add your ContextForge database URL"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi

# Apply environment ConfigMap
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml
echo "[OK] ConfigMap applied"
echo ""

# Apply Secret
echo "Applying Secret..."
kubectl apply -f secret.yaml
echo "[OK] Secret applied"
echo ""

# Apply plugins ConfigMap
if [ ! -f "$PLUGIN_CONFIG_PATH" ]; then
    echo "Error: plugin config not found at $PLUGIN_CONFIG_PATH"
    exit 1
fi

echo "Applying plugins ConfigMap..."
kubectl create configmap context-forge-plugins \
    -n "$NAMESPACE" \
    --from-file=config.yaml="$PLUGIN_CONFIG_PATH" \
    --dry-run=client -o yaml | kubectl apply -f -
echo "[OK] Plugins ConfigMap applied"
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
echo "  Next Steps"
echo "================================================"
echo ""
echo "Wait for the pod to be ready:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "Port-forward to access the UI/API:"
echo "  kubectl port-forward -n $NAMESPACE svc/context-forge 4444:4444"
echo ""
echo "[OK] Deployment complete"
