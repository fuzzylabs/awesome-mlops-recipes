#!/bin/bash
set -e

echo "================================================"
echo "  Removing Prometheus + Grafana"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

kubectl delete -f rag-api-servicemonitor.yaml --ignore-not-found
kubectl delete -f grafana-dashboard-configmap.yaml --ignore-not-found
helm uninstall monitoring -n monitoring || true

if kubectl get namespace monitoring &> /dev/null; then
  kubectl delete namespace monitoring
fi

echo "[OK] Monitoring stack removed"
