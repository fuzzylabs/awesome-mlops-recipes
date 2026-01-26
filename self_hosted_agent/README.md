# 🕵️‍♀️ Self-Hosted PR Review Agent

This recipe cooks up a PR review agent running on Kubernetes, powered by vLLM for model serving and MLflow for prompt management.

This recipe is split into two parts that build on each other:
- Part 1 (Prototype): vLLM, MLflow prompt management, evals, and basic observability.
- Part 2 (Production governance): MCP ContextForge gateway with fine-grained tool policies and provenance.

**Cook Time**: ~1 Hour

## 🥗 Ingredients

### Part 1: Prototype
- **Agent Framework**: Pydantic AI
- **Model Serving**: vLLM
- **Evaluation**: Pydantic Evals
- **Observability**: Pydantic Logfire
- **Prompt Management**: MLflow

### Part 2: Production governance
- **MCP Gateway + Policy Engine**: IBM MCP ContextForge
- **Tool Policy Enforcement**: Schema Guard + rate limits
- **Provenance**: ContextForge tool telemetry exporter (OpenTelemetry)

## 🗄️ Project Structure

```
.
├── src/                    # Agent source code & FastAPI server
├── evals/                  # Evaluation suites (LLM judge, span-based)
├── llm/                    # vLLM server Dockerfile
├── context_forge/          # ContextForge policy config (Part 2)
├── prompt_versioning/      # Prompt versioning helper scripts
├── k8s/                    # Kubernetes manifests
│   ├── vllm/              # vLLM deployment
│   ├── logfire_backend/   # Jaeger backend
│   ├── agent/             # Agent deployment
│   └── context_forge/     # ContextForge gateway (Part 2)
└── helm/                   # Helm charts
    └── mlflow/            # MLflow installation
```

## ☁️ Infrastructure Requirements

This recipe requires the following AWS resources:

- **EKS Cluster** - Kubernetes cluster with one CPU node and one GPU node
- **RDS PostgreSQL** - Managed database for MLflow tracking
- **S3 Bucket** - Object storage for MLflow artifacts
- **ECR Repositories** - Two container registries for Docker images (agent and vLLM)
- **VPC** - Isolated network environment with public and private subnets
- **IAM Roles** - Service roles for secure authentication

💡 **Quick Setup**: We provide ready-to-use Infrastructure as Code using Pulumi: [awesome-mlops-recipes-iac](https://github.com/fuzzylabs/awesome-mlops-recipes-iac)

Part 2 reuses the same AWS resources and runs in the same Kubernetes cluster.

## ✅ Prerequisites

1. **Kubernetes cluster** (EKS with 1 GPU node for vLLM and 1 CPU node for Agent and MLFlow)
2. **AWS credentials** configured
3. **kubectl** configured for your cluster
4. **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
5. **make** - Build automation tool (usually pre-installed on macOS/Linux)

## ✍️ Placeholder Values to Update

Use outputs from the IaC repo (`awesome-mlops-recipes-iac/self_hosted_agent/pulumi`) for RDS endpoints and ECR URIs.
If you only run Part 1, you can ignore the Part 2 ContextForge placeholders.

**IaC outputs you'll use:**
- `agentServerEcrUrl`
- `vllmServerEcrUrl`
- `mlflowDbEndpoint`
- `mlflowDbName`
- `mlflowDbUsername`

The MLflow database password is stored in Pulumi config:
```bash
pulumi config get mlflowDbPassword
```

**Secrets & config files to edit:**
- `self_hosted_agent/helm/mlflow/mlflow.env` (copy from `mlflow.env.example`)
  - `MLFLOW_DB_ENDPOINT`
  - `MLFLOW_DB_NAME`
  - `MLFLOW_DB_USERNAME`
  - `MLFLOW_DB_PASSWORD` (Pulumi secret)
  - `MLFLOW_S3_BUCKET`
  - `MLFLOW_S3_ROLE_ARN`
- `self_hosted_agent/k8s/agent/secret.yaml` (copy from `secret.yaml.example`)
  - GitHub token for tool access
- `self_hosted_agent/k8s/context_forge/secret.yaml` (copy from `secret.yaml.example`, Part 2)
  - `DATABASE_URL` for the ContextForge Postgres database

**Optional (Part 2 auth + gateway wiring):**
- `self_hosted_agent/k8s/context_forge/configmap.yaml`
  - `AUTH_REQUIRED` and JWT settings (if enabling gateway auth)
- `self_hosted_agent/src/config.yaml` or `self_hosted_agent/k8s/agent/configmap.yaml`
  - `mcp.gateway_url` (ContextForge `/mcp` endpoint)
  - `mcp.gateway_auth_token` (if `AUTH_REQUIRED=true`)

**Kubernetes image URIs:**
- `self_hosted_agent/k8s/agent/deployment.yaml` -> `agentServerEcrUrl`
- `self_hosted_agent/k8s/vllm/deployment.yaml` -> `vllmServerEcrUrl`

## 🚀 Quick Start

Complete Steps 1-6 for the prototype. Stop after Step 6 if you do not want the production governance add-on (Part 2).

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

This registers a new prompt in MLflow named `pr-review-agent-system-prompt`. You can customise the prompt template in [`prompt_versioning/new.py`](prompt_versioning/new.py).

To update the prompt later with a new version:
```bash
# Edit the prompt in prompt_versioning/update.py
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

### 4. Deploy Logfire backend

Logfire uses the OpenTelemetry standard. This means that you can configure the SDK to export to any backend that supports OpenTelemetry. To keep it simple, we will use [this](https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends/) guide to host [Jaeger](https://www.jaegertracing.io/). But you can use any backend you like or just use pydantic close source platform to start with.

```bash
make deploy-jaeger
```

Port forward the Jaeger UI.

```bash
make portforward-jaeger
```

### 5. Deploy the Agent

Create the GitHub token secret first:
```bash
cd k8s/agent
cp secret.yaml.example secret.yaml
# Edit secret.yaml with your GitHub token
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

### 6. Test the Agent

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

You should now be able to see the agent traces in the Jaeger UI.

## Part 2: Production Governance (ContextForge)

### Manual Steps Checklist

- Create the `context_forge` database and `context_forge_user` on the existing RDS instance.
- Create `k8s/context_forge/secret.yaml` with the ContextForge `DATABASE_URL`.
- Register the GitHub MCP server in ContextForge and expose only the required tools.
- Point the agent at the gateway by setting `mcp.gateway_url`.

### 1. Deploy ContextForge

First, create a dedicated database and user in the existing RDS instance (from the IaC stack). If you already have a `psql` client, you can use:
```sql
CREATE DATABASE context_forge;
CREATE USER context_forge_user WITH PASSWORD '<strong-password>';
GRANT ALL PRIVILEGES ON DATABASE context_forge TO context_forge_user;
```

Otherwise, spin up an ephemeral pod:
```bash
kubectl run -it --rm psql \
  --image=postgres:16 \
  --restart=Never \
  --env="FEEDBACK_DB_DSN=postgresql://<mlflowDbEndpoint>/mlflow" \
  -- bash
```

Then connect to the RDS instance:
```bash
psql $FEEDBACK_DB_DSN -U mlflow
```

Then, exit the ephemeral pod by:
```bash
exit
```

Finally, create the dedicated database using the SQL command above.

You can connect using the MLflow RDS endpoint and admin credentials from the IaC outputs.

Then, create the Kubernetes secret:
```bash
cd k8s/context_forge
cp secret.yaml.example secret.yaml
# Edit secret.yaml and set DATABASE_URL with the RDS endpoint, user, and password
cd ../..
```

Deploy the gateway and policy engine:
```bash
make deploy-context-forge
make wait-context-forge
```

Port forward the ContextForge UI/API:
```bash
make portforward-context-forge
```

The default `k8s/context_forge/configmap.yaml` disables auth for quick setup. For production, set `AUTH_REQUIRED=true` and configure JWT settings in the same ConfigMap.

### 2. Configure Tool Policies

Edit the policy configuration in `context_forge/plugins/config.yaml`. The defaults enable:
- Rate limits per tool
- Schema validation (permissive by default)
- Tool-call telemetry export (OpenTelemetry)

Once the schemas match your GitHub MCP tool definitions, switch Schema Guard to `enforce`.

Re-deploy to apply updates:
```bash
make deploy-context-forge
```

### 3. Register the GitHub MCP Server and Tools

Use the ContextForge API to register the GitHub MCP server and expose only the tools your agent needs:
- `search_pull_requests`
- `pull_request_read`
- `pull_request_review_write`

Store the upstream GitHub token in ContextForge during registration so the agent never sees it.

To register:
```bash
export GITHUB_TOKEN="<YOUR_GITHUB_TOKEN"

curl -s -X POST http://localhost:4444/gateways \
  -H "Content-Type: application/json" \
  -d '{
        "name": "github-mcp",
        "url": "https://api.githubcopilot.com/mcp/",
        "transport": "STREAMABLEHTTP",
        "auth_type": "bearer",
        "auth_token": "'"$GITHUB_TOKEN"'"
      }'
```

Get the registered gateway ID:
```bash
curl -s http://localhost:4444/gateways | jq
```

List tools discovered via that gateway:
```bash
curl -s "http://localhost:4444/tools?gateway_id=<GATEWAY_ID>&limit=0" | jq
```

Create a virtual server with just the allowed tools:
```bash
curl -s -X POST http://localhost:4444/servers \
  -H "Content-Type: application/json" \
  -d '{
        "server": {
          "name": "github-pr-review",
          "description": "Allowlisted GitHub tools",
          "associated_tools": [
            "ac909d70771942f79a4dc20e65fd1b9d",
            "13930074f3d0485d8b4ea8fc6922df74",
            "b489773abba446819eb029f580bb9e5b"
          ]
        }
      }' | jq
```


### 4. Point the Agent at the Gateway

Update `src/config.yaml` (local) or `k8s/agent/configmap.yaml` (Kubernetes):
```yaml
mcp:
  gateway_url: "http://context-forge.context-forge.svc.cluster.local:4444/servers/<VIRTUAL_SERVER_UUID>/mcp"
  gateway_auth_token: ""
  gateway_forward_github_token: false
```

For k8s, apply the updated conifgmap:
```bash
kubectl apply -f k8s/agent/configmap.yaml
```

> **Auth Note:** If you enable `AUTH_REQUIRED` in the gateway, set `gateway_auth_token` (or `MCP_GATEWAY_TOKEN`) so the agent can authenticate.

### 5. Verify Governance + Provenance

- Tool calls should now flow through ContextForge with allowlisted tools and schema validation.
- Tool invocation telemetry is exported to Jaeger/Logfire via OpenTelemetry.
- Restart the agent after pointing it at the ContextForge virtual server:
```bash
make restart-agent
```
- Port-forward the agent, ContextForge, and Jaeger UIs (In separate terminals):
```bash
make portforward-agent
make portforward-context-forge
make portforward-jaeger
```
- Invoke the agent and verify tool calls are routed through the gateway:
```bash
curl -X POST http://localhost:8080/review \
  -H "Content-Type: application/json" \
  -d '{"pr_title": "Fix authentication flow"}'
```
- Check ContextForge logs and Jaeger traces for tool-call activity:
```bash
make logs-context-forge
```

## 🎯 Evaluation

Run the LLM judge evaluation suite:

> **Note:** Make sure to port-forward required services first (keep them running in separate terminals):
> ```bash
> make portforward-mlflow  # Required for logging results
> make portforward-vllm    # Required if using vLLM provider
> ```

Export your GitHub and Anthropic tokens:
```bash
export GITHUB_TOKEN=""
export ANTHROPIC_API_KEY=""
```

The LLM judge model is currently set to Claude Sonnet 4.5, which requires an `ANTHROPIC_API_KEY`. You can change this to any model that suits your needs. For details on model selection, see the [LLM Judge documentation](https://ai.pydantic.dev/evals/evaluators/llm-judge/#model-selection).

Then, run:
```bash
make eval-review-quality
```

## 🧪 Experimentation

### Iterating on System Prompts

The agent loads its system prompt from MLflow at startup. Here's how to experiment with different prompt versions:

**1. Update your prompt**

Edit the prompt template in `prompt_versioning/update.py`, then register the new version:
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
- MCP gateway settings (ContextForge URL + auth)

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
- `make deploy-context-forge` - Deploy ContextForge gateway (Part 2)

**Port Forwarding:**
- `make portforward-mlflow` - Access MLflow UI (localhost:5000)
- `make portforward-vllm` - Access vLLM (localhost:8000)
- `make portforward-agent` - Access agent API (localhost:8080)
- `make portforward-context-forge` - Access ContextForge (localhost:4444)

**Evaluation:**
- `make eval-review-quality` - Run LLM judge evaluation

**Monitoring:**
- `make logs-vllm` - Stream vLLM logs
- `make logs-agent` - Stream agent logs
- `make logs-context-forge` - Stream ContextForge logs

**Teardown:**
- `make teardown-vllm` - Remove vLLM deployment
- `make teardown-agent` - Remove agent deployment
- `make teardown-context-forge` - Remove ContextForge deployment

## 🧹 Teardown

To remove deployments:
```bash
make teardown-agent
make teardown-vllm
make teardown-context-forge
```
