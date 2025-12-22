.PHONY: deploy-mlflow create-new-prompt update-prompt setup-vllm deploy-jaeger setup-agent portforward-vllm portforward-jaeger portforward-agent portforward-mlflow eval-review-quality teardown-vllm teardown-agent logs-agent logs-vllm restart-agent wait-mlflow wait-vllm wait-agent status-mlflow status-vllm status-agent help

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

# Setup logfire backend (deploy)
deploy-jaeger:
	@echo "Deploying Jaeger backend to Kubernetes..."
	cd k8s/logfire_backend && ./deploy.sh

# Setup agent (build + push + deploy)
setup-agent:
	@echo "Building and pushing agent image..."
	cd src && ./build-and-push.sh
	@echo "Deploying agent to Kubernetes..."
	cd k8s/agent && ./deploy.sh

# Port forward vllm service
portforward-vllm:
	@echo "Port forwarding vLLM service to localhost:8000..."
	kubectl port-forward svc/qwen3 8000:8000 -n vllm

portforward-jaeger:
	@echo "Port forwarding Jaeger service to localhost:16686..."
	kubectl port-forward svc/logfire-backend 16686:16686 -n logfire

# Port forward services
portforward-agent:
	@echo "Port forwarding agent service to localhost:8080..."
	kubectl port-forward svc/pr-review-agent 8080:8080 -n agent

portforward-mlflow:
	@echo "Port forwarding MLflow service to localhost:5000..."
	kubectl port-forward svc/mlflow 5000:5000 -n mlflow

# Run evaluations
eval-review-quality:
	@echo "Running LLM judge evaluation..."
	uv run python evals/llm_judge/review_quality.py

# Teardown resources
teardown-vllm:
	@echo "Tearing down vLLM resources..."
	cd k8s/vllm && ./teardown.sh

teardown-agent:
	@echo "Tearing down agent resources..."
	cd k8s/agent && ./teardown.sh

# View logs
logs-agent:
	@echo "Streaming agent logs..."
	kubectl logs -f deployment/pr-review-agent -n agent

logs-vllm:
	@echo "Streaming vLLM logs..."
	kubectl logs -f deployment/qwen3 -n vllm

# Restart deployments
restart-agent:
	@echo "Restarting agent deployment..."
	kubectl rollout restart deployment pr-review-agent -n agent

# Watch pod status
wait-mlflow:
	@echo "Watching MLflow pods..."
	kubectl get pods -n mlflow -w

wait-vllm:
	@echo "Watching vLLM pods..."
	kubectl get pods -n vllm -w

wait-agent:
	@echo "Watching agent pods..."
	kubectl get pods -n agent -w

# Check pod status
status-mlflow:
	@echo "MLflow pod status:"
	kubectl get pods -n mlflow

status-vllm:
	@echo "vLLM pod status:"
	kubectl get pods -n vllm

status-agent:
	@echo "Agent pod status:"
	kubectl get pods -n agent

# Help
help:
	@echo "Available targets:"
	@echo ""
	@echo "Setup & Deployment:"
	@echo "  deploy-mlflow        - Deploy MLflow"
	@echo "  create-new-prompt    - Register new system prompt (requires port-forward)"
	@echo "  update-prompt        - Update prompt version (requires port-forward)"
	@echo "  setup-vllm           - Build and deploy vLLM server"
	@echo "  setup-agent          - Build and deploy PR review agent"
	@echo ""
	@echo "Port Forwarding:"
	@echo "  portforward-mlflow   - Port forward MLflow (localhost:5000)"
	@echo "  portforward-vllm     - Port forward vLLM (localhost:8000)"
	@echo "  portforward-agent    - Port forward agent (localhost:8080)"
	@echo ""
	@echo "Evaluation:"
	@echo "  eval-review-quality  - Run LLM judge evaluation"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs-vllm            - Stream vLLM logs"
	@echo "  logs-agent           - Stream agent logs"
	@echo "  status-mlflow        - Check MLflow pod status"
	@echo "  status-vllm          - Check vLLM pod status"
	@echo "  status-agent         - Check agent pod status"
	@echo "  wait-mlflow          - Watch MLflow pods (blocking)"
	@echo "  wait-vllm            - Watch vLLM pods (blocking)"
	@echo "  wait-agent           - Watch agent pods (blocking)"
	@echo ""
	@echo "Management:"
	@echo "  restart-agent        - Restart agent deployment"
	@echo ""
	@echo "Teardown:"
	@echo "  teardown-vllm        - Remove vLLM deployment"
	@echo "  teardown-agent       - Remove agent deployment"

