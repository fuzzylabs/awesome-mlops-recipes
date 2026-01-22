# Locust Load Testing

Part 2 add-on for the RAG stack.
This folder deploys Locust in-cluster to load test the RAG API.
Edit `load_testing/locustfile.py` to change the workload before deployment; the deploy script creates the ConfigMap from that file.

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
