# Self-Hosted RAG Stack

This recipe is split into two parts that build on each other:
- Part 1 (Prototype): vLLM, Chroma, Metaflow ingestion, MLflow prompt tracking, RAGAS evals, and basic guardrails (hallucination + jailbreak).
- Part 2 (Production add-ons): Ray Serve, monitoring, load testing, a feedback loop agent, and business-specific guardrails (financial advice).

Cook Time: ~1-2 hours (excluding model download and indexing)

## Ingredients

### Part 1: Prototype
- Data pipeline: Metaflow (Kubernetes)
- Vector DB: Chroma
- Embeddings: BAAI/bge-large-en-v1.5
- Reranker: BAAI/bge-reranker-base
- Model serving: vLLM (Qwen/Qwen3-4B-Thinking-2507)
- Prompt management: MLflow
- Evaluation: RAGAS + Guardrails AI (hallucination, jailbreak)

### Part 2: Production add-ons
- Model proxy: Ray Serve (vLLM behind Ray Serve; RAG API stays outside)
- Monitoring: Prometheus + Grafana
- Load testing: Locust
- Feedback loop: Pydantic AI + Postgres
- Business guardrails: Guardrails AI (financial advice, enabled at runtime in Part 2)

## Project Structure

```
.
├── src/                    # RAG API + retrieval/generation logic (Part 1)
├── evals/                  # RAGAS + guardrails (Part 1 + Part 2)
├── feedback_loop/          # Feedback agent + schema (Part 2)
├── load_testing/           # Locust workload (Part 2)
├── llm/                    # vLLM server Dockerfile (Part 1)
├── ray_serve/              # Ray Serve proxy Dockerfile (Part 2)
├── prompt_versioning/      # Prompt versioning helper scripts (Part 1; Part 2 updates)
├── data_pipeline/          # Metaflow flows (ingest -> parse -> chunk -> embed -> index) (Part 1)
├── k8s/                    # Kubernetes manifests
│   ├── vllm/              # vLLM deployment (Part 1)
│   ├── chroma/            # Chroma deployment (Part 1)
│   ├── rag-api/           # RAG API deployment (Part 1)
│   ├── metaflow/          # Metaflow deployment (Part 1)
│   ├── ray-serve/          # Ray Serve deployment (Part 2)
│   ├── monitoring/         # Prometheus + Grafana (Part 2)
│   └── locust/             # Locust load testing (Part 2)
└── helm/                   # MLflow installation (Part 1)
    └── mlflow/            # MLflow installation scripts
```

## Infrastructure Requirements

This recipe assumes the AWS infrastructure is provisioned using the IaC repo:
https://github.com/fuzzylabs/awesome-mlops-recipes-iac

Expected resources:
- EKS cluster (CPU + GPU node group)
- RDS PostgreSQL (shared between MLflow and Metaflow, two databases)
- S3 bucket (MLflow artifacts + Chroma snapshots)
- ECR repositories (rag-api, rag-vllm-server, rag-metaflow, rag-rayserve)
- VPC + IAM roles for service access

Part 2 reuses the same AWS resources. The feedback loop can share the existing RDS instance (or use a separate database if you prefer).

## Prerequisites

1. Kubernetes cluster (EKS with 1 GPU node and 1 CPU node)
2. AWS credentials configured
3. kubectl configured for your cluster
4. uv (Python package manager)
5. make
6. helm

## Placeholder Values to Update

You will need to replace placeholders in the files below. Use IaC outputs (Pulumi stack outputs) to source values like ECR URLs, S3 bucket names, and RDS endpoints. If you only run Part 1, you can ignore the Part 2 placeholders noted below. Example:
```bash
cd awesome-mlops-recipes-iac/rag_stack/pulumi
pulumi stack output
```

Expected outputs for the `rag_stack` stack:
- `ragApiEcrUrl`
- `ragVllmServerEcrUrl`
- `ragMetaflowEcrUrl`
- `ragRayserveEcrUrl` (Part 2)
- `mlflowS3Bucket`
- `mlflowS3RoleArn`
- `metaflowS3RoleArn`
- `chromaSnapshotRoleArn`
- `mlflowDbEndpoint`
- `mlflowDbName`
- `mlflowDbUsername`

The database password is stored in Pulumi config:
```bash
pulumi config get mlflowDbPassword
```

ECR image URIs:
- `k8s/vllm/deployment.yaml` -> `ragVllmServerEcrUrl`
- `k8s/rag-api/deployment.yaml` -> `ragApiEcrUrl`
- `k8s/metaflow/deployment.yaml` -> `ragMetaflowEcrUrl`
- `k8s/ray-serve/rayservice.yaml` -> `ragRayserveEcrUrl` (Part 2)

S3 bucket + prefix:
- `data_pipeline/config.yaml` -> `s3.bucket`, `s3.prefix` (use `mlflowS3Bucket`, `rag-stack/chroma-snapshots`)
- `k8s/chroma/snapshot-job.yaml` -> `S3_BUCKET` and `S3_PREFIX` (use `mlflowS3Bucket`, `rag-stack/chroma-snapshots`)
- `k8s/chroma/restore-job.yaml` -> `S3_BUCKET` and `S3_PREFIX` (use `mlflowS3Bucket`, `rag-stack/chroma-snapshots`)
- `k8s/metaflow/configmap.yaml` -> `METAFLOW_DATASTORE_SYSROOT_S3`, `METAFLOW_DATATOOLS_SYSROOT_S3` (use `mlflowS3Bucket`)

RDS + credentials:
- `helm/mlflow/mlflow.env` -> `mlflowDbEndpoint`, `mlflowDbName`, `mlflowDbUsername` + `mlflowDbPassword`
- `k8s/metaflow/configmap.yaml` -> `MF_METADATA_DB_HOST`, `MF_METADATA_DB_USER`, `MF_METADATA_DB_NAME` (use `mlflowDbEndpoint`, `mlflowDbUsername`, set DB name to `metaflow`)
- `k8s/metaflow/secret.yaml` -> `MF_METADATA_DB_PSWD` (use `mlflowDbPassword`)
- Create the `metaflow` database on the shared RDS instance (separate from `mlflow`)

IRSA role ARNs:
- `k8s/metaflow/serviceaccount.yaml` -> `metaflowS3RoleArn`
- `k8s/chroma/serviceaccount.yaml` -> `chromaSnapshotRoleArn`
- `helm/mlflow/mlflow.env` -> `mlflowS3RoleArn`

Other placeholders:
- `src/config.yaml` -> `generation.base_url` (Part 1: vLLM service; Part 2: Ray Serve URL)
- `src/config.yaml` -> `guardrails.financial_advice_enabled` (Part 2 only; keep `false` for Part 1)
- `k8s/monitoring/values.yaml` -> `grafana.adminPassword` (Part 2)
- `FEEDBACK_DB_DSN` -> Postgres DSN for the shared RDS instance (Part 2; use the existing `metaflow` database unless you create a separate one)

## Part 1: Prototype Quick Start

Complete these steps for the prototype. Stop after Step 8 if you do not want the production add-ons.

### 1. Deploy MLflow

```bash
cd helm/mlflow
cp mlflow.env.example mlflow.env
# Do not include the endpoint port number in MLFLOW_DB_ENDPOINT
```
Edit mlflow.env with your values, then:
```bash
source mlflow.env
cd ../..
make deploy-mlflow
```

### 2. Deploy Metaflow (metadata service + UI)

Metaflow runs as a service in Kubernetes and uses the shared RDS instance. The deployment pulls the `rag-metaflow` image from ECR, so you must build and push it first:
```bash
make build-pipeline-image
```

Then configure and deploy. Set the required environment variables from your Pulumi outputs,:
```bash
cd /path/to/awesome-mlops-recipes-iac/rag_stack/pulumi
export METAFLOW_S3_BUCKET=$(pulumi stack output mlflowS3Bucket)
export METAFLOW_RDS_ENDPOINT=$(pulumi stack output mlflowDbEndpoint)
export METAFLOW_DB_PASSWORD=$(pulumi config get mlflowDbPassword)
export METAFLOW_S3_ROLE_ARN=$(pulumi stack output metaflowS3RoleArn)
export RAG_METAFLOW_ECR_URL=$(pulumi stack output ragMetaflowEcrUrl)
cd /path/to/awesome-mlops-recipes/rag_stack
make configure-metaflow
make setup-metaflow
```

You can port-forward the service for local access:
```bash
make portforward-metaflow
```

### 3. Register the RAG system prompt

Port-forward MLflow in a separate terminal:
```bash
make portforward-mlflow
```

Then register the prompt:
```bash
make create-new-prompt
```

This registers the Part 1 prompt. Part 2 updates it with business-specific guardrails via the feedback loop or `make update-prompt`.

### 4. Deploy vLLM

Update the image in `k8s/vllm/deployment.yaml` to match your ECR repository before deploying.

```bash
make setup-vllm
make wait-vllm
```

### 5. Deploy Chroma

```bash
make setup-chroma
```

### 6. Build and run the Metaflow pipeline (manual trigger)

```bash
make build-pipeline-image
make run-pipeline
```

Update `data_pipeline/config.yaml` with your S3 bucket before running the pipeline. The pipeline ingests a 50-document subset of FinDER, chunks and embeds, writes to Chroma, and snapshots the index to S3. It keeps the last 3 snapshots.

Set `chroma.rebuild` to `false` if you want to append to an existing collection instead of clearing it on each run.

For Kubernetes execution, set these environment variables in your shell or Metaflow config:
- `METAFLOW_KUBERNETES_IMAGE` (ECR image built by `make build-pipeline-image`)
- `METAFLOW_SERVICE_URL` (Metaflow metadata service URL)
- `METAFLOW_DEFAULT_METADATA=service`
- `METAFLOW_DEFAULT_DATASTORE=s3`
- `METAFLOW_DATASTORE_SYSROOT_S3` (e.g., `s3://<bucket>/metaflow`)
- `METAFLOW_DATATOOLS_SYSROOT_S3` (e.g., `s3://<bucket>/metaflow`)
- `CHROMA_PERSIST_DIR` (optional, path to Chroma data if you mount the PVC)

If you do not mount the Chroma PVC into the pipeline pods, use the snapshot job in the next step.

### 7. Snapshot or Restore Chroma

Snapshot the current Chroma index to S3 and keep the last 3 snapshots:
```bash
make snapshot-chroma
```

Update the bucket and prefix in `k8s/chroma/snapshot-job.yaml` and `k8s/chroma/restore-job.yaml` before running. The snapshot and restore jobs use the `chroma-snapshot` service account in `k8s/chroma/serviceaccount.yaml` to access S3 via IRSA. If your AWS CLI image lacks `tar`, switch the job image to one that includes it.

Restore the latest snapshot (scale down Chroma first):
```bash
kubectl scale deployment/chroma -n chroma --replicas=0
make restore-chroma
kubectl scale deployment/chroma -n chroma --replicas=1
```

### 8. Deploy the RAG API

Update the image in `k8s/rag-api/deployment.yaml` to match your ECR repository before deploying.

```bash
make setup-rag-api
make wait-rag-api
```

Port-forward and test:
```bash
make portforward-rag-api
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the revenue of Company X in 2023?"}'
```

## Part 2: Production Add-ons

These steps assume Part 1 is deployed and running.

### 9. Put vLLM behind Ray Serve

Install the KubeRay operator (once per cluster):
```bash
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update
helm upgrade --install kuberay-operator kuberay/kuberay-operator -n kuberay --create-namespace
```

Build and deploy the Ray Serve proxy:
```bash
make build-rayserve-image
make setup-ray
```

Update `src/config.yaml` so `generation.base_url` points at Ray Serve:
```
http://rayserve-vllm-serve-svc.rayserve.svc.cluster.local:8000/v1
```

Rebuild and redeploy the RAG API to pick up the change:
```bash
make setup-rag-api
```

### 10. Enable monitoring (Prometheus + Grafana)

```bash
make setup-monitoring
```

The RAG API exposes Prometheus metrics at `/metrics`. The ServiceMonitor in `k8s/monitoring/rag-api-servicemonitor.yaml` scrapes it automatically.

Port-forward Grafana and Prometheus:
```bash
make portforward-grafana
make portforward-prometheus
```

### 11. Run load tests with Locust

```bash
make setup-locust
make portforward-locust
```

Edit `load_testing/locustfile.py` to adjust the workload before deploying.

### 12. Feedback loop (manual trigger)

Create the feedback table on the shared RDS instance:
```bash
psql "$FEEDBACK_DB_DSN" -f feedback_loop/schema.sql
```

Run the feedback agent to propose a prompt update:
```bash
export OPENAI_API_KEY="local"
make run-feedback-agent
```

Approve the proposed prompt after review:
```bash
make approve-feedback-prompt
```

## Evaluation

### Part 1: RAGAS + basic guardrails

Run the prototype evaluation suite:
```bash
make eval-rag-part1
```

This logs RAGAS metrics plus Guardrails AI hallucination/jailbreak checks to MLflow. Update `evals/ragas/config.yaml` to match the FinDER fields, and edit the JSONL files under `evals/guardrails/` for guardrail prompts.

### Part 2: Business guardrails + feedback loop

Use the feedback loop agent to propose a prompt update (or run `make update-prompt`), then approve it:
```bash
make run-feedback-agent
make approve-feedback-prompt
```

Enable the runtime financial advice guardrail (Part 2 only) in `src/config.yaml`:
```yaml
guardrails:
  financial_advice_enabled: true
```

Restart the RAG API deployment so it loads the updated prompt:
```bash
kubectl rollout restart deployment/rag-api -n rag-api
```

Re-run evals with the business-specific guardrails:
```bash
make eval-rag-part2
```

Part 2 evals include the Part 1 suite plus financial advice checks in `evals/guardrails/financial_advice.py` with cases in `evals/guardrails/financial_advice_cases.jsonl`.

If your API is not port-forwarded to localhost, set `RAG_API_URL` before running guardrail checks.
If MLflow is not port-forwarded to localhost, set `MLFLOW_TRACKING_URI` before running evals.

## Experimentation

- Update retrieval settings in `src/config.yaml`
- Update the prompt in `prompt_versioning/update.py`
- Compare runs in MLflow

## Configuration

- `src/config.yaml` controls vector DB, retrieval, and generation settings
- `data_pipeline/config.yaml` controls dataset subset and pipeline settings
- `evals/ragas/config.yaml` controls RAGAS dataset extraction
- `llm/Dockerfile` controls the vLLM model and runtime

## Available Commands

Run `make help` to see all commands.

## Teardown

```bash
make teardown-rag-api
make teardown-chroma
make teardown-vllm
make teardown-metaflow
```
