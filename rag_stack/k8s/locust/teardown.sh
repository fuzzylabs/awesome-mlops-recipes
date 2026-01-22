#!/bin/bash
set -e

echo "================================================"
echo "  Tearing Down Locust"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="locust"

kubectl delete -f service.yaml --ignore-not-found
kubectl delete -f deployment.yaml --ignore-not-found
kubectl delete configmap locustfile -n "$NAMESPACE" --ignore-not-found

if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    kubectl delete namespace "$NAMESPACE"
fi

echo "[OK] Locust resources deleted"
