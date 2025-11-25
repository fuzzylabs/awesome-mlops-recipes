"""PR review Agent."""

import logfire
import mlflow
from pydantic_ai import Agent, RunContext

from model import get_anthropic_model
from tools import github_server, filter_github_tools

# Configure observability
logfire.configure()
logfire.instrument_pydantic_ai()

# Load prompt from MLflow at module level (before tracing starts)
_prompt = mlflow.genai.load_prompt("pr-review-agent-system-prompt")
SYSTEM_PROMPT = _prompt.template

# Create the PR review agent
pr_review_agent = Agent(
    get_anthropic_model(),
    toolsets=[github_server],
    prepare_tools=filter_github_tools,
)


# Attach system prompt
@pr_review_agent.system_prompt
async def get_system_prompt(ctx: RunContext[None]) -> str:
    """Return the PR review prompt loaded from MLflow."""
    return SYSTEM_PROMPT


if __name__ == '__main__':
    # Only run the agent when executing this file directly
    result = pr_review_agent.run_sync(
        'Review the pull request titled "Add Ollama provider support for local LLM inference"'
    )
    print(result.output)
