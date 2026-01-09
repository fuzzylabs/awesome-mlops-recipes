#!/bin/bash
set -e

echo "================================================"
echo "  Installing Prometheus + Grafana"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace \
  -f values.yaml

kubectl apply -f rag-api-servicemonitor.yaml
kubectl apply -f grafana-dashboard-configmap.yaml

echo "[OK] Monitoring stack installed"
