# 🕵️‍♀️ Self-Hosted PR Review Agent

This recipe cooks up a PR review agent running on Kubernetes, powered by vLLM for model serving and MLflow for prompt management.

> NOTE: The recipe does not include IaC (TODO, point people to one?).

## 🥗 Ingredients

- **Agent Framework**: Pydantic AI
- **Model Serving**: vLLM
- **Evaluation**: Pydantic Evals
- **Observability**: Pydantic Logfire
- **Prompt Management**: MLflow

## 🗄️ Project Structure

```
.
├── src/                    # Agent source code & FastAPI server
├── evals/                  # Evaluation suites (LLM judge, span-based)
├── llm/                    # vLLM server Dockerfile
├── prmopt_versioning       # prompt versioning helper scripts
├── k8s/                    # Kubernetes manifests
│   ├── vllm/              # vLLM deployment
│   └── agent/             # Agent deployment
└── helm/                   # Helm charts
    └── mlflow/            # MLflow installation
```

## ✅ Prerequisites

1. **Kubernetes cluster** (EKS with GPU nodes for vLLM)
2. **AWS credentials** configured
3. **kubectl** configured for your cluster
4. **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
5. **make** - Build automation tool (usually pre-installed on macOS/Linux)

## 🚀 Quick Start

### 1. Deploy MLflow

First, configure your MLflow backend:

```bash
cd helm/mlflow
cp mlflow.env.example mlflow.env
# Edit mlflow.env with your values
source mlflow.env
```

Deploy MLflow:
```bash
make deploy-mlflow
```

### 2. Register Your System Prompt

First, port-forward MLflow (keep this running in a separate terminal):

```bash
make portforward-mlflow
```

Then, create the initial system prompt for your agent:

```bash
make create-new-prompt
```

This registers a new prompt in MLflow named `pr-review-agent-system-prompt`. You can customise the prompt template in [`prmopt_versioning/new.py`](prmopt_versioning/new.py).

To update the prompt later with a new version:
```bash
# Edit the prompt in prmopt_versioning/update.py
make update-prompt
```

You can also manage prompts via the MLflow UI at [http://localhost:5000](http://localhost:5000) (while port-forwarded).

### 3. Deploy vLLM Server

Configure your model in `llm/Dockerfile`, then:
```bash
make setup-vllm
```

This will:
- Build the vLLM Docker image
- Push to ECR
- Deploy to Kubernetes

Check logs:
```bash
make logs-vllm
```

### 4. Deploy the Agent

Create Kubernetes secrets first:
```bash
cd k8s/agent
cp secret.yaml.example secret.yaml
# Edit secret.yaml with your tokens
```

Then deploy:
```bash
make setup-agent
```

This will:
- Build the agent Docker image
- Push to ECR
- Deploy to Kubernetes

Check logs:
```bash
make logs-agent
```

### 5. Test the Agent

Port forward the agent service:
```bash
make portforward-agent
```

Test with curl:
```bash
curl -X POST http://localhost:8080/review \
  -H "Content-Type: application/json" \
  -d '{"pr_title": "Add new feature"}'
```

## 🎯 Evaluation

Run the LLM judge evaluation suite:
```bash
make eval-review-quality
```

Results are logged to MLflow for tracking prompt performance across versions.

## ⚙️ Configuration

### Agent Configuration

Edit `src/config.yaml` to configure:
- Model provider (anthropic, vllm, ollama)
- Model parameters
- MLflow settings

### vLLM Configuration

Edit `llm/Dockerfile` to configure:
- Model name
- vLLM parameters (`--max-model-len`, `--max-num-batched-tokens`, etc.)

We wrote this recipe using the 4 billion parameter thinking version of Qwen3, but you can use any model you prefer. You’ll probably want one that handles function calling well, so check the leaderboard below for good options.

**References:**
- [Function Calling Leaderboard](https://huggingface.co/spaces/gorilla-llm/berkeley-function-calling-leaderboard)

## 💻 Available Commands

Run `make help` to see all commands, or use these common ones:

**Setup & Deployment:**
- `make deploy-mlflow` - Deploy MLflow
- `make create-new-prompt` - Register new system prompt
- `make update-prompt` - Update prompt version
- `make setup-vllm` - Build and deploy vLLM server
- `make setup-agent` - Build and deploy agent

**Port Forwarding:**
- `make portforward-mlflow` - Access MLflow UI (localhost:5000)
- `make portforward-vllm` - Access vLLM (localhost:8000)
- `make portforward-agent` - Access agent API (localhost:8080)

**Evaluation:**
- `make eval-review-quality` - Run LLM judge evaluation

**Monitoring:**
- `make logs-vllm` - Stream vLLM logs
- `make logs-agent` - Stream agent logs

**Teardown:**
- `make teardown-vllm` - Remove vLLM deployment
- `make teardown-agent` - Remove agent deployment

## 🧹 Teardown

To remove deployments:
```bash
make teardown-agent
make teardown-vllm
```
