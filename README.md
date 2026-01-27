# MLOps Recipes

A collection of self-contained MLOps recipes for the COOKING WITH MLOps book. Each project is independent and includes a dedicated README with setup and execution instructions.

This repository contains the code and instructions needed to run each recipe from the book.

In addition, you can find the Infrastructure as Code repository used to provision the required resources for recipes three through six [here](https://github.com/fuzzylabs/awesome-mlops-recipes-iac)

## Recipes

### Recipe One: Experiment in Computer Vision
Lightweight CV experiment tracking with reproducible data + runs.
- DVC data versioning, MLflow tracking, ZenML pipelines, Git for code
- Example dataset flows for grayscale/RGB and a run logbook for iteration notes
See `experiment_in_computer_vision/README.md`

### Recipe Two: Fashion on the Edge
Train, quantise, and deploy a tiny vision model to edge hardware.
- Optuna HPO, PyTorch + Brevitas QAT, MLflow tracking, ZenML local pipelines
- ONNX -> TensorFlow -> TFLite int8 export; optional ESP32 deployment via PlatformIO
See `vision_on_the_edge/README.md`

### Recipe Three & Four: Self-Hosted Agent
PR review agent running on Kubernetes with evals, prompt management, and optional governance.
- Part 1: Pydantic AI agent, vLLM model serving, MLflow prompt versioning, Logfire/Jaeger observability
- Part 2: ContextForge MCP gateway with tool policy enforcement and provenance
See `self_hosted_agent/README.md`


### Recipe Five & Six: RAG Stack
Prototype-to-production RAG system on Kubernetes with evaluation, guardrails, and ops add-ons.
- Part 1: Metaflow ingestion, Chroma, vLLM serving, MLflow prompt tracking, RAGAS + Guardrails evals
- Part 2: Ray Serve proxy, Prometheus/Grafana monitoring, Locust load testing, feedback-loop agent, business guardrails
- Infra: AWS EKS + RDS + S3 + ECR (IaC repo referenced in the project)
See `rag_stack/README.md`
