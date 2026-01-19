# Metaflow on Kubernetes

This folder contains a minimal Metaflow metadata service deployment that runs inside your cluster and uses the shared RDS instance and S3 bucket.

## Files

- `Dockerfile` - Lightweight Metaflow service image (~200 MB)
- `build-and-push.sh` - Builds and pushes the service image to ECR
- `configmap.yaml` - Metaflow service configuration (S3 + DB settings)
- `secret.yaml.example` - DB password for Metaflow
- `serviceaccount.yaml` - IRSA role for S3 access
- `deployment.yaml` - Metaflow metadata service
- `service.yaml` - ClusterIP service
- `configure.sh` - Configures manifests from environment variables
- `deploy.sh` / `teardown.sh` - helper scripts

## Image

This folder contains a **lightweight** Dockerfile for the Metaflow metadata service (~200 MB). It only includes `metaflow` and `boto3` - not the heavy pipeline dependencies like `sentence-transformers` (PyTorch).

Build and push the service image:
```bash
./build-and-push.sh
# Or from rag_stack/: make build-metaflow-service-image
```

The full pipeline image (`make build-pipeline-image` from `data_pipeline/`) is only needed when running the actual data pipeline, not for the metadata service.

## Quick Start (Automated)

Set environment variables from Pulumi outputs and run the configure script:
```bash
export METAFLOW_S3_BUCKET=$(pulumi stack output mlflowS3Bucket)
export METAFLOW_RDS_ENDPOINT=$(pulumi stack output mlflowDbEndpoint)
export METAFLOW_DB_PASSWORD=$(pulumi config get mlflowDbPassword)
export METAFLOW_S3_ROLE_ARN=$(pulumi stack output metaflowS3RoleArn)
export RAG_METAFLOW_ECR_URL=$(pulumi stack output ragMetaflowEcrUrl)
./configure.sh
./deploy.sh
```

## Manual Updates (placeholders)

If you prefer to update manually, change these values before deploying:

1. `configmap.yaml`
   - `METAFLOW_DATASTORE_SYSROOT_S3` and `METAFLOW_DATATOOLS_SYSROOT_S3`
     - Use the S3 bucket from IaC outputs (same bucket as MLflow is OK)
   - `MF_METADATA_DB_HOST`
     - Use the RDS endpoint from IaC outputs
   - `MF_METADATA_DB_USER`, `MF_METADATA_DB_NAME`
     - Create a second DB in RDS named `metaflow` (separate from `mlflow`)

2. `secret.yaml`
   - Copy `secret.yaml.example` to `secret.yaml` and set `MF_METADATA_DB_PSWD`
   - Use the same RDS password you configured in IaC

3. `serviceaccount.yaml`
   - Replace the IRSA role ARN with the Metaflow S3 access role

4. `deployment.yaml`
   - Replace the image with your Metaflow service image (ECR) built by `make build-metaflow-service-image`.

## Deploy

```bash
./deploy.sh
```

If you want the pipeline to snapshot Chroma directly, mount the Chroma PVC into the Metaflow job pods and set `CHROMA_PERSIST_DIR=/chroma/chroma` in your Metaflow configuration.

Check status:
```bash
kubectl get pods -n metaflow -w
```

Port-forward the service:
```bash
kubectl port-forward -n metaflow svc/metaflow 8080:8080
```

## Database Setup

Create the Metaflow database on the shared RDS instance:
```bash
CREATE DATABASE metaflow;
```

Ensure the `metaflow` user has access to the database.
