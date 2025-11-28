"""PR review Agent."""

import logfire
from pydantic_ai import Agent, RunContext

from model import get_model
from tools import github_server, filter_github_tools
from prompt import SYSTEM_PROMPT


# Configure observability
logfire.configure()
logfire.instrument_pydantic_ai()

# Create the PR review agent with model from config
pr_review_agent = Agent(
    get_model(),  # Automatically uses provider from config.yaml
    toolsets=[github_server],
    prepare_tools=filter_github_tools,
)


# Attach system prompt
@pr_review_agent.system_prompt
async def get_system_prompt(ctx: RunContext[None]) -> str:
    """Return the PR review prompt loaded from MLflow."""
    return SYSTEM_PROMPT


if __name__ == '__main__':
    result = pr_review_agent.run_sync(
        'Review the pull request titled "Add Ollama provider support for local LLM inference"'
    )
    print(result.output)
