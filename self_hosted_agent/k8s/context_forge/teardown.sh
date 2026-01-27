#!/bin/bash
set -e

echo "================================================"
echo "  Tearing Down ContextForge"
echo "================================================"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
NAMESPACE="context-forge"

# Confirm deletion
echo "This will delete:"
echo "  - ContextForge deployment and pods"
echo "  - Service"
echo "  - ConfigMaps"
echo "  - Secret"
echo "  - Namespace $NAMESPACE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Teardown cancelled."
    exit 0
fi

# Delete resources in reverse order
echo "Deleting Service..."
kubectl delete -f service.yaml --ignore-not-found=true
echo "[OK] Service deleted"
echo ""

echo "Deleting Deployment..."
kubectl delete -f deployment.yaml --ignore-not-found=true
echo "[OK] Deployment deleted"
echo ""

echo "Deleting ConfigMaps..."
kubectl delete -f configmap.yaml --ignore-not-found=true
kubectl delete configmap context-forge-plugins -n "$NAMESPACE" --ignore-not-found=true
echo "[OK] ConfigMaps deleted"
echo ""

echo "Deleting Secret..."
kubectl delete -f secret.yaml --ignore-not-found=true 2>/dev/null || echo "[SKIP] Secret not found"
echo "[OK] Secret deleted"
echo ""

echo "Deleting Namespace..."
kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
echo "[OK] Namespace deleted"
echo ""

echo "================================================"
echo "  Teardown Complete"
echo "================================================"
echo ""
echo "[OK] All ContextForge resources have been removed"
