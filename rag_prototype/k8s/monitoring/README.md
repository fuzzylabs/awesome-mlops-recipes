# Monitoring (Prometheus + Grafana)

This folder installs Prometheus and Grafana using the kube-prometheus-stack Helm chart, plus a ServiceMonitor and a basic RAG API dashboard.

## Required Updates

- Update `values.yaml` and set a secure Grafana admin password.

## Install

```bash
./install.sh
```

## Port-forward

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Grafana login:
- user: `admin`
- password: from `values.yaml`

## Teardown

```bash
./teardown.sh
```
