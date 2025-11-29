# 🕵️‍♀️ Self-Hosted PR Review Agent

This recipe cooks up a PR review agent running on Kubernetes, powered by vLLM for model serving and MLflow for prompt management.

**Cook Time**: ~1 Hour

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
├── prmopt_versioning/      # Prompt versioning helper scripts
├── k8s/                    # Kubernetes manifests
│   ├── vllm/              # vLLM deployment
│   └── agent/             # Agent deployment
└── helm/                   # Helm charts
    └── mlflow/            # MLflow installation
```

## ✅ Prerequisites

1. **Kubernetes cluster** (EKS with 1 GPU node for vLLM and 1 CPU node for Agent and MLFlow)
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
```
Edit mlflow.env with your values, then:
```bash
source mlflow.env
cd ../..
```


Deploy MLflow:
```bash
make deploy-mlflow
```

Wait for the MLflow container to be ready:
```bash
make wait-mlflow
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

You can configure a model of your choice in [`llm/Dockerfile`](llm/Dockerfile), default is `Qwen/Qwen3-4B-Thinking-2507`, then:
```bash
make setup-vllm
```

This will:
- Build the vLLM Docker image (this will take ~20 minutes)
- Push to ECR
- Deploy to Kubernetes

Wait for it to start and become ready (~8 minutes):
```bash
make wait-vllm
```

Check logs to verify the model server is ready to take requests (~4 minutes). You should see the `/health` endpoint getting hit when it's ready:
```bash
make logs-vllm
```

### 4. Deploy the Agent

Create Kubernetes secrets first:
```bash
cd k8s/agent
cp secret.yaml.example secret.yaml
# Edit secret.yaml with your tokens
cd ../..
```

Then deploy:
```bash
make setup-agent
```

This will:
- Build the agent Docker image
- Push to ECR
- Deploy to Kubernetes

Wait for it to start and become ready:
```bash
make wait-agent
```

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

> **Note:** Make sure to port-forward required services first (keep them running in separate terminals):
> ```bash
> make portforward-mlflow  # Required for logging results
> make portforward-vllm    # Required if using vLLM provider
> ```

Export your Logfire and GitHub token:
```bash
export LOGFIRE_TOKEN=""
export GITHUB_TOKEN=""
```

Then, run:
```bash
make eval-review-quality
```

## 🧪 Experimentation

### Iterating on System Prompts

The agent loads its system prompt from MLflow at startup. Here's how to experiment with different prompt versions:

**1. Update your prompt**

Edit the prompt template in `prmopt_versioning/update.py`, then register the new version:
```bash
make portforward-mlflow  # If not already running
make update-prompt
```

**2. Run evaluation**

Test the new prompt version locally:
```bash
make eval-review-quality
```

Results are logged to MLflow, allowing you to compare performance across prompt versions.

**3. Deploy the updated prompt**

To use the **latest** prompt version in your deployed agent:
```bash
make restart-agent
```

To use a **specific** prompt version, update `prompt_version` in `src/config.yaml` or `k8s/agent/configmap.yaml`, then:
```bash
make restart-agent
```

### Comparing Results

Use the MLflow UI to compare evaluation metrics across prompt versions:
```bash
make portforward-mlflow
# Open http://localhost:5000 and navigate to Experiments
```

## ⚙️ Configuration

### Agent Configuration

Edit `src/config.yaml` to configure:
- Model provider (vllm, ollama)
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
