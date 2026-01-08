.PHONY: deploy-mlflow create-new-prompt update-prompt setup-vllm setup-chroma setup-rag-api setup-metaflow build-pipeline-image run-pipeline build-eval-data snapshot-chroma restore-chroma portforward-vllm portforward-chroma portforward-rag-api portforward-metaflow portforward-mlflow eval-rag teardown-vllm teardown-chroma teardown-rag-api teardown-metaflow logs-vllm logs-rag-api logs-metaflow wait-mlflow wait-vllm wait-chroma wait-rag-api wait-metaflow status-mlflow status-vllm status-chroma status-rag-api status-metaflow help

# Deploy MLflow
deploy-mlflow:
	@echo "Deploying MLflow..."
	cd helm/mlflow && ./install.sh

# Create new prompt (requires MLflow to be port-forwarded)
create-new-prompt:
	@echo "Creating new prompt..."
	@echo "Make sure MLflow is port-forwarded (run 'make portforward-mlflow' in another terminal)"
	@sleep 2
	uv run prompt_versioning/new.py

# Update prompt version (requires MLflow to be port-forwarded)
update-prompt:
	@echo "Updating prompt version..."
	@echo "Make sure MLflow is port-forwarded (run 'make portforward-mlflow' in another terminal)"
	@sleep 2
	uv run prompt_versioning/update.py

# Setup vLLM (build + push + deploy)
setup-vllm:
	@echo "Building and pushing vLLM image..."
	cd llm && ./build-and-push.sh
	@echo "Deploying vLLM to Kubernetes..."
	cd k8s/vllm && ./deploy.sh

# Setup Chroma
setup-chroma:
	@echo "Deploying Chroma to Kubernetes..."
	cd k8s/chroma && ./deploy.sh

# Setup Metaflow
setup-metaflow:
	@echo "Deploying Metaflow service..."
	cd k8s/metaflow && ./deploy.sh

# Build pipeline image for Metaflow
build-pipeline-image:
	@echo "Building and pushing Metaflow pipeline image..."
	cd data_pipeline && ./build-and-push.sh

# Run Metaflow pipeline (manual trigger)
run-pipeline:
	@echo "Running Metaflow pipeline..."
	uv run python data_pipeline/flow.py run --with kubernetes

# Build evaluation data
build-eval-data:
	@echo "Building RAGAS evaluation dataset..."
	uv run python evals/ragas/build_eval_data.py

# Setup RAG API (build + push + deploy)
setup-rag-api:
	@echo "Building and pushing RAG API image..."
	cd src && ./build-and-push.sh
	@echo "Deploying RAG API to Kubernetes..."
	cd k8s/rag-api && ./deploy.sh

# Port forward services
portforward-mlflow:
	@echo "Port forwarding MLflow service to localhost:5000..."
	kubectl port-forward svc/mlflow 5000:5000 -n mlflow

portforward-vllm:
	@echo "Port forwarding vLLM service to localhost:8000..."
	kubectl port-forward svc/qwen3 8000:8000 -n vllm

portforward-chroma:
	@echo "Port forwarding Chroma service to localhost:8000..."
	kubectl port-forward svc/chroma 8000:8000 -n chroma

portforward-rag-api:
	@echo "Port forwarding RAG API service to localhost:8080..."
	kubectl port-forward svc/rag-api 8080:8080 -n rag-api

portforward-metaflow:
	@echo "Port forwarding Metaflow service to localhost:8080..."
	kubectl port-forward svc/metaflow 8080:8080 -n metaflow

# Run evaluations
eval-rag:
	@echo "Running RAG evaluation suite..."
	uv run python evals/ragas/build_eval_data.py
	uv run python evals/ragas/run.py
	uv run python evals/guardrails/hallucination.py
	uv run python evals/guardrails/jailbreak.py

# Snapshot and restore Chroma
snapshot-chroma:
	@echo "Creating Chroma snapshot..."
	kubectl delete job/chroma-snapshot -n chroma --ignore-not-found
	kubectl apply -f k8s/chroma/snapshot-job.yaml
	kubectl wait --for=condition=complete job/chroma-snapshot -n chroma --timeout=10m
	kubectl delete job/chroma-snapshot -n chroma

restore-chroma:
	@echo "Restoring Chroma snapshot..."
	kubectl delete job/chroma-restore -n chroma --ignore-not-found
	kubectl apply -f k8s/chroma/restore-job.yaml
	kubectl wait --for=condition=complete job/chroma-restore -n chroma --timeout=10m
	kubectl delete job/chroma-restore -n chroma

# Teardown resources
teardown-vllm:
	@echo "Tearing down vLLM resources..."
	cd k8s/vllm && ./teardown.sh

teardown-chroma:
	@echo "Tearing down Chroma resources..."
	cd k8s/chroma && ./teardown.sh

teardown-rag-api:
	@echo "Tearing down RAG API resources..."
	cd k8s/rag-api && ./teardown.sh

teardown-metaflow:
	@echo "Tearing down Metaflow resources..."
	cd k8s/metaflow && ./teardown.sh

# View logs
logs-vllm:
	@echo "Streaming vLLM logs..."
	kubectl logs -f deployment/qwen3 -n vllm

logs-rag-api:
	@echo "Streaming RAG API logs..."
	kubectl logs -f deployment/rag-api -n rag-api

logs-metaflow:
	@echo "Streaming Metaflow logs..."
	kubectl logs -f deployment/metaflow -n metaflow

# Watch pod status
wait-mlflow:
	@echo "Watching MLflow pods..."
	kubectl get pods -n mlflow -w

wait-vllm:
	@echo "Watching vLLM pods..."
	kubectl get pods -n vllm -w

wait-chroma:
	@echo "Watching Chroma pods..."
	kubectl get pods -n chroma -w

wait-rag-api:
	@echo "Watching RAG API pods..."
	kubectl get pods -n rag-api -w

wait-metaflow:
	@echo "Watching Metaflow pods..."
	kubectl get pods -n metaflow -w

# Check pod status
status-mlflow:
	@echo "MLflow pod status:"
	kubectl get pods -n mlflow

status-vllm:
	@echo "vLLM pod status:"
	kubectl get pods -n vllm

status-chroma:
	@echo "Chroma pod status:"
	kubectl get pods -n chroma

status-rag-api:
	@echo "RAG API pod status:"
	kubectl get pods -n rag-api

status-metaflow:
	@echo "Metaflow pod status:"
	kubectl get pods -n metaflow

# Help
help:
	@echo "Available targets:"
	@echo ""
	@echo "Setup & Deployment:"
	@echo "  deploy-mlflow        - Deploy MLflow"
	@echo "  create-new-prompt    - Register new system prompt (requires port-forward)"
	@echo "  update-prompt        - Update prompt version (requires port-forward)"
	@echo "  setup-metaflow       - Deploy Metaflow service"
	@echo "  build-pipeline-image - Build and push Metaflow pipeline image"
	@echo "  run-pipeline         - Run Metaflow pipeline (manual trigger)"
	@echo "  build-eval-data      - Build RAGAS evaluation dataset"
	@echo "  setup-vllm           - Build and deploy vLLM server"
	@echo "  setup-chroma         - Deploy Chroma server"
	@echo "  setup-rag-api        - Build and deploy RAG API"
	@echo ""
	@echo "Port Forwarding:"
	@echo "  portforward-mlflow   - Port forward MLflow (localhost:5000)"
	@echo "  portforward-vllm     - Port forward vLLM (localhost:8000)"
	@echo "  portforward-chroma   - Port forward Chroma (localhost:8000)"
	@echo "  portforward-rag-api  - Port forward RAG API (localhost:8080)"
	@echo "  portforward-metaflow - Port forward Metaflow (localhost:8080)"
	@echo ""
	@echo "Evaluation:"
	@echo "  eval-rag             - Run RAG evaluation suite"
	@echo ""
	@echo "Chroma Snapshot:"
	@echo "  snapshot-chroma      - Snapshot Chroma to S3"
	@echo "  restore-chroma       - Restore latest Chroma snapshot"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs-vllm            - Stream vLLM logs"
	@echo "  logs-rag-api         - Stream RAG API logs"
	@echo "  logs-metaflow        - Stream Metaflow logs"
	@echo "  status-mlflow        - Check MLflow pod status"
	@echo "  status-vllm          - Check vLLM pod status"
	@echo "  status-chroma        - Check Chroma pod status"
	@echo "  status-rag-api       - Check RAG API pod status"
	@echo "  status-metaflow      - Check Metaflow pod status"
	@echo "  wait-mlflow          - Watch MLflow pods (blocking)"
	@echo "  wait-vllm            - Watch vLLM pods (blocking)"
	@echo "  wait-chroma          - Watch Chroma pods (blocking)"
	@echo "  wait-rag-api         - Watch RAG API pods (blocking)"
	@echo "  wait-metaflow        - Watch Metaflow pods (blocking)"
	@echo ""
	@echo "Teardown:"
	@echo "  teardown-vllm        - Remove vLLM deployment"
	@echo "  teardown-chroma      - Remove Chroma deployment"
	@echo "  teardown-rag-api     - Remove RAG API deployment"
	@echo "  teardown-metaflow    - Remove Metaflow deployment"
