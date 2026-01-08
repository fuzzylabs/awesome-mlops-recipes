#!/bin/bash
set -e

echo "================================================"
echo "  Tearing Down Ray Serve"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NAMESPACE="rayserve"

kubectl delete -f rayservice.yaml --ignore-not-found

if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    kubectl delete namespace "$NAMESPACE"
fi

echo "[OK] Ray Serve resources deleted"
