#!/bin/bash
set -e

echo "================================================"
echo "  Tearing Down Chroma"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="chroma"

kubectl delete -f service.yaml --ignore-not-found
kubectl delete -f deployment.yaml --ignore-not-found
kubectl delete -f pvc.yaml --ignore-not-found

if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    kubectl delete namespace "$NAMESPACE"
fi

echo "[OK] Chroma resources deleted"
