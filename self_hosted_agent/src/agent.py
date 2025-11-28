"""PR review Agent."""

import logfire
from pydantic_ai import Agent, RunContext

from model import get_model
from tools import github_server, filter_github_tools
from prompt import load_prompt
from config import get_config



def initialise_agent() -> tuple[Agent, str]:
    """Initialise the PR review agent."""
    # Load config
    cfg = get_config()

    # Configure observability
    logfire.configure(token=cfg.logfire.token)
    logfire.instrument_pydantic_ai()

    # Create the PR review agent with model from config
    pr_review_agent = Agent(
        get_model(),  # Automatically uses provider from config.yaml
        toolsets=[github_server],
        prepare_tools=filter_github_tools,
    )

    # Load prompt
    prompt_template, prompt_version = load_prompt()

    # Attach system prompt
    @pr_review_agent.system_prompt
    async def get_system_prompt(ctx: RunContext[None]) -> str:
        """Return the PR review prompt loaded from MLflow."""
        return prompt_template
    
    return pr_review_agent, prompt_version


if __name__ == '__main__':
    pr_review_agent, _ = initialise_agent()
    result = pr_review_agent.run_sync(
        'Review the pull request titled "Add Ollama provider support for local LLM inference"'
    )
    print(result.output)
