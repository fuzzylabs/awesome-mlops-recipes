from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.mcp import MCPServerStreamableHTTP
import logfire
import os

logfire.configure()  
logfire.instrument_pydantic_ai()

ollama_model = OpenAIChatModel(
    model_name='qwen3:4b-thinking-2507-fp16',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),  
)

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
model = AnthropicModel(
    'claude-sonnet-4-5', provider=AnthropicProvider(api_key=os.getenv('ANTHROPIC_API_KEY'))
)

# Filter to only allow PR review related tools
async def filter_github_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition]:
    """Only allow tools needed for PR review"""
    allowed_tools = {
        'search_pull_requests',     # Search PRs by title
        'pull_request_read',        # Get PR details with different methods
        'pull_request_review_write', # Write operations (create, submit, delete) on pull request reviews.
    }
    return [tool_def for tool_def in tool_defs if tool_def.name in allowed_tools]

# Agent-side MCP server (works with Ollama)
github_server = MCPServerStreamableHTTP(
    'https://api.githubcopilot.com/mcp/',
    headers={'Authorization': 'Bearer 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'}
)

pr_review_agent = Agent(  
    model,
    toolsets=[github_server],
    prepare_tools=filter_github_tools,
)

@pr_review_agent.system_prompt
async def provide_instructions(ctx: RunContext[None]) -> str:
    """Dynamic instructions for PR review"""
    return """You are an expert pull request reviewer for the fuzzylabs/sre-agent repository.

REPO SUMMARY:
sre-agent is an AI SRE tool that monitors Kubernetes deployments, diagnoses issues, and reports findings. It uses Python 3.12+, TypeScript, FastAPI, and MCP servers.

TOOLS YOU CAN USE:
- search_pull_requests: find PRs
- pull_request_read:
  * get: basic PR info
  * get_diff: code changes
  * get_files: list of changed files
  * get_review_comments: comments on the diff
  * get_comments: general comments
  * get_reviews: reviews
  * get_status: build and check status
- pull_request_review_write: submit the review

REVIEW STEPS:
1. Search for the PR
2. Read basic PR details
3. Check the list of changed files
4. Review the diff
5. Submit your review with pull_request_review_write

WHAT TO LOOK FOR:
- Code quality in Python and TypeScript
- Fit with the existing architecture
- Security concerns
- Test coverage and test quality
- Performance impact
- Documentation updates
- Kubernetes patterns where relevant
- MCP server patterns where relevant

RULES:
- Only review PRs in fuzzylabs/sre-agent
- Give clear and actionable feedback based on the actual changes
"""


if __name__ == '__main__':
    # Only run the agent when executing this file directly
    result = pr_review_agent.run_sync('Review the pull request titled "Add Ollama provider support for local LLM inference"')
    print(result.output)
