# Feedback Loop Agent (Pydantic AI)

Part 2 add-on for the RAG stack.
This folder contains a lightweight feedback agent that proposes prompt updates based on user feedback stored in Postgres. Use it to introduce business-specific guardrails such as blocking financial advice.

## Database

Create a simple feedback table on the shared RDS instance (reuse the existing `metaflow` database unless you want to provision another one):

```sql
-- Use the output from feedback_loop/schema.sql
```

Set the database connection string:

```bash
export FEEDBACK_DB_DSN="postgresql://user:password@host:5432/metaflow"
```

If `FEEDBACK_DB_DSN` is not set, the agent falls back to `sample_feedback.jsonl`.

## Propose a prompt update

```bash
export MLFLOW_TRACKING_URI="http://localhost:5000"
export PROMPT_NAME="rag-stack-system-prompt"
export MODEL_BASE_URL="http://rayserve-vllm-serve-svc.rayserve.svc.cluster.local:8000/v1"
export OPENAI_API_KEY="local"

uv run feedback_loop/agent.py
```

This registers a new prompt version in MLflow with `status=proposed`.

## Approve a prompt update

```bash
export MLFLOW_TRACKING_URI="http://localhost:5000"
export PROMPT_NAME="rag-stack-system-prompt"
export PROMPT_STATUS="approved"

uv run feedback_loop/approve_prompt.py
```

This marks the prompt as approved/production (two-step workflow).
