#!/bin/bash
set -e

echo "================================================"
echo "  Tearing Down vLLM Deployment"
echo "================================================"
echo ""

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
NAMESPACE="vllm"

# Confirm deletion
echo "This will delete:"
echo "  - vLLM deployment and pods"
echo "  - Service"
echo "  - PersistentVolumeClaim (and associated EBS volume)"
echo "  - StorageClass gp3"
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

echo "Deleting PVC (this will delete the EBS volume)..."
kubectl delete -f pvc.yaml --ignore-not-found=true
echo "[OK] PVC deleted"
echo ""

echo "Deleting StorageClass..."
kubectl delete -f storage-class-gp3.yaml --ignore-not-found=true
echo "[OK] StorageClass deleted"
echo ""

echo "Deleting Namespace..."
kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
echo "[OK] Namespace deleted"
echo ""

echo "================================================"
echo "  Teardown Complete"
echo "================================================"
echo ""
echo "[OK] All vLLM resources have been removed"
