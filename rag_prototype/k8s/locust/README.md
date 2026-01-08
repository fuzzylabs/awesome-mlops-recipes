# Locust Load Testing

This folder deploys Locust in-cluster to load test the RAG API.

## Deploy

```bash
./deploy.sh
```

Port-forward the UI:
```bash
kubectl port-forward -n locust svc/locust 8089:8089
```

Open http://localhost:8089 to start a test.

## Teardown

```bash
./teardown.sh
```
