# Ray Serve (vLLM proxy)

This folder deploys Ray Serve as a lightweight proxy in front of vLLM. The RAG API calls Ray Serve, and Ray Serve forwards requests to vLLM.

## Prerequisites

Install the KubeRay operator:
```bash
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update
helm upgrade --install kuberay-operator kuberay/kuberay-operator -n kuberay --create-namespace
```

## Build the Ray Serve image

```bash
cd ray_serve
./build-and-push.sh
```

Update the image in `rayservice.yaml` before deploying.

## Deploy

```bash
./deploy.sh
```

Ray Serve exposes a service named `rayserve-vllm-serve-svc` in the `rayserve` namespace. Use this URL as the model base URL for the RAG API.

Example:
```
http://rayserve-vllm-serve-svc.rayserve.svc.cluster.local:8000
```
