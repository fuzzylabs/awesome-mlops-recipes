#!/bin/bash
set -e

echo "================================================"
echo "  Tearing Down Metaflow Service"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="metaflow"

kubectl delete -f service.yaml --ignore-not-found
kubectl delete -f deployment.yaml --ignore-not-found
kubectl delete -f configmap.yaml --ignore-not-found
kubectl delete -f serviceaccount.yaml --ignore-not-found
kubectl delete -f secret.yaml --ignore-not-found

if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    kubectl delete namespace "$NAMESPACE"
fi

echo "[OK] Metaflow resources deleted"
