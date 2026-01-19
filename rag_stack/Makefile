.PHONY: deploy-mlflow create-new-prompt update-prompt setup-vllm setup-chroma setup-rag-api configure-metaflow setup-metaflow build-pipeline-image run-pipeline build-eval-data snapshot-chroma restore-chroma setup-ray build-rayserve-image setup-monitoring setup-locust run-feedback-agent approve-feedback-prompt portforward-vllm portforward-chroma portforward-rag-api portforward-mlflow portforward-metaflow portforward-rayserve portforward-grafana portforward-prometheus portforward-locust eval-rag eval-rag-part1 eval-rag-part2 teardown-vllm teardown-chroma teardown-rag-api teardown-metaflow teardown-ray teardown-monitoring teardown-locust logs-vllm logs-rag-api logs-metaflow wait-mlflow wait-vllm wait-chroma wait-rag-api wait-metaflow status-mlflow status-vllm status-chroma status-rag-api status-metaflow help

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

# Configure Metaflow manifests from environment variables
configure-metaflow:
	@echo "Configuring Metaflow manifests..."
	@echo "Required env vars: METAFLOW_S3_BUCKET, METAFLOW_RDS_ENDPOINT, METAFLOW_DB_PASSWORD, METAFLOW_S3_ROLE_ARN, RAG_METAFLOW_ECR_URL"
	cd k8s/metaflow && ./configure.sh

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

# Ray Serve for vLLM
build-rayserve-image:
	@echo "Building and pushing Ray Serve image..."
	cd ray_serve && ./build-and-push.sh

setup-ray:
	@echo "Deploying Ray Serve..."
	cd k8s/ray-serve && ./deploy.sh

# Monitoring
setup-monitoring:
	@echo "Installing Prometheus + Grafana..."
	cd k8s/monitoring && ./install.sh

# Locust
setup-locust:
	@echo "Deploying Locust..."
	cd k8s/locust && ./deploy.sh

# Feedback loop
run-feedback-agent:
	@echo "Running feedback loop agent..."
	uv run feedback_loop/agent.py

approve-feedback-prompt:
	@echo "Approving prompt in MLflow..."
	uv run feedback_loop/approve_prompt.py

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

portforward-rayserve:
	@echo "Port forwarding Ray Serve to localhost:8000..."
	kubectl port-forward svc/rayserve-vllm-serve-svc 8000:8000 -n rayserve

portforward-grafana:
	@echo "Port forwarding Grafana to localhost:3000..."
	kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

portforward-prometheus:
	@echo "Port forwarding Prometheus to localhost:9090..."
	kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring

portforward-locust:
	@echo "Port forwarding Locust to localhost:8089..."
	kubectl port-forward svc/locust 8089:8089 -n locust

# Run evaluations
eval-rag-part1:
	@echo "Running Part 1 RAG evaluation suite..."
	uv run python evals/ragas/build_eval_data.py
	uv run python evals/ragas/run.py
	uv run python evals/guardrails/hallucination.py
	uv run python evals/guardrails/jailbreak.py

eval-rag-part2: export RUN_FINANCIAL_ADVICE_GUARDRAIL=1
eval-rag-part2: eval-rag-part1
	@echo "Running Part 2 guardrails (financial advice)..."

eval-rag: eval-rag-part2

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

teardown-ray:
	@echo "Tearing down Ray Serve..."
	cd k8s/ray-serve && ./teardown.sh

teardown-monitoring:
	@echo "Tearing down monitoring stack..."
	cd k8s/monitoring && ./teardown.sh

teardown-locust:
	@echo "Tearing down Locust..."
	cd k8s/locust && ./teardown.sh

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
	@echo "  deploy-mlflow          - Deploy MLflow"
	@echo "  create-new-prompt      - Register new system prompt (requires port-forward)"
	@echo "  update-prompt          - Update prompt version (requires port-forward)"
	@echo "  configure-metaflow     - Configure Metaflow manifests from env vars"
	@echo "  setup-metaflow         - Deploy Metaflow service"
	@echo "  build-pipeline-image   - Build and push Metaflow pipeline image"
	@echo "  run-pipeline           - Run Metaflow pipeline (manual trigger)"
	@echo "  build-eval-data        - Build RAGAS evaluation dataset"
	@echo "  setup-vllm             - Build and deploy vLLM server"
	@echo "  setup-chroma           - Deploy Chroma server"
	@echo "  setup-rag-api          - Build and deploy RAG API"
	@echo "  build-rayserve-image   - Build and push Ray Serve image"
	@echo "  setup-ray              - Deploy Ray Serve"
	@echo "  setup-monitoring       - Install Prometheus + Grafana"
	@echo "  setup-locust           - Deploy Locust"
	@echo "  run-feedback-agent     - Run the feedback loop agent"
	@echo "  approve-feedback-prompt - Approve a proposed prompt"
	@echo ""
	@echo "Port Forwarding:"
	@echo "  portforward-mlflow     - Port forward MLflow (localhost:5000)"
	@echo "  portforward-vllm       - Port forward vLLM (localhost:8000)"
	@echo "  portforward-chroma     - Port forward Chroma (localhost:8000)"
	@echo "  portforward-rag-api    - Port forward RAG API (localhost:8080)"
	@echo "  portforward-metaflow   - Port forward Metaflow (localhost:8080)"
	@echo "  portforward-rayserve   - Port forward Ray Serve (localhost:8000)"
	@echo "  portforward-grafana    - Port forward Grafana (localhost:3000)"
	@echo "  portforward-prometheus - Port forward Prometheus (localhost:9090)"
	@echo "  portforward-locust     - Port forward Locust (localhost:8089)"
	@echo ""
	@echo "Evaluation:"
	@echo "  eval-rag-part1         - Run Part 1 evals (RAGAS + hallucination/jailbreak)"
	@echo "  eval-rag-part2         - Run Part 2 evals (Part 1 + financial advice)"
	@echo "  eval-rag               - Run full eval suite (alias for Part 2)"
	@echo ""
	@echo "Chroma Snapshot:"
	@echo "  snapshot-chroma        - Snapshot Chroma to S3"
	@echo "  restore-chroma         - Restore latest Chroma snapshot"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs-vllm              - Stream vLLM logs"
	@echo "  logs-rag-api           - Stream RAG API logs"
	@echo "  logs-metaflow          - Stream Metaflow logs"
	@echo "  status-mlflow          - Check MLflow pod status"
	@echo "  status-vllm            - Check vLLM pod status"
	@echo "  status-chroma          - Check Chroma pod status"
	@echo "  status-rag-api         - Check RAG API pod status"
	@echo "  status-metaflow        - Check Metaflow pod status"
	@echo "  wait-mlflow            - Watch MLflow pods (blocking)"
	@echo "  wait-vllm              - Watch vLLM pods (blocking)"
	@echo "  wait-chroma            - Watch Chroma pods (blocking)"
	@echo "  wait-rag-api           - Watch RAG API pods (blocking)"
	@echo "  wait-metaflow          - Watch Metaflow pods (blocking)"
	@echo ""
	@echo "Teardown:"
	@echo "  teardown-vllm          - Remove vLLM deployment"
	@echo "  teardown-chroma        - Remove Chroma deployment"
	@echo "  teardown-rag-api       - Remove RAG API deployment"
	@echo "  teardown-metaflow      - Remove Metaflow deployment"
	@echo "  teardown-ray           - Remove Ray Serve deployment"
	@echo "  teardown-monitoring    - Remove Prometheus + Grafana"
	@echo "  teardown-locust        - Remove Locust"
