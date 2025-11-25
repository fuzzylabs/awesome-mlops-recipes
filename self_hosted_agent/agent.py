from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.mcp import MCPServerStreamableHTTP
import logfire

logfire.configure()  
logfire.instrument_pydantic_ai()

ollama_model = OpenAIChatModel(
    model_name='qwen3:4b-thinking-2507-fp16',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),  
)

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
model = AnthropicModel(
    'claude-sonnet-4-5', provider=AnthropicProvider(api_key='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')
)

# Filter to only allow PR review related tools
async def filter_github_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition]:
    """Only allow tools needed for PR review"""
    allowed_tools = {
        'search_pull_requests',     # Search PRs by title
        'pull_request_read',        # Get PR details with different methods
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
    return """You are an expert code reviewer for the fuzzylabs/sre-agent repository.

REPOSITORY CONTEXT:
The sre-agent is a Site Reliability Engineer AI agent that monitors Kubernetes deployments, 
diagnoses issues, and reports diagnostics. Tech stack: Python 3.12+, TypeScript, FastAPI, MCP servers.

AVAILABLE TOOLS:
- search_pull_requests: Search for PRs by query/title
- pull_request_read: Get PR data with these methods:
  * method="get" - Get basic PR details
  * method="get_diff" - Get the unified diff showing code changes
  * method="get_files" - Get list of changed files
  * method="get_review_comments" - Get review comments on the diff
  * method="get_comments" - Get general PR comments
  * method="get_reviews" - Get PR reviews
  * method="get_status" - Get build/check status

YOUR REVIEW WORKFLOW:
1. Use search_pull_requests to find the PR number in fuzzylabs/sre-agent repository
2. Use pull_request_read with method="get" to get PR details (owner="fuzzylabs", repo="sre-agent", pullNumber=X)
3. Use pull_request_read with method="get_files" to see what files were changed
4. Use pull_request_read with method="get_diff" to examine the actual code changes
5. Optionally use method="get_review_comments" or method="get_comments" for context
6. Provide a structured review covering:

REVIEW FOCUS AREAS:
✅ Code Quality: Python/TypeScript best practices, readability, maintainability
✅ Architecture: Does it fit the existing agent architecture?
✅ Security: Any security concerns or vulnerabilities?
✅ Testing: Are there tests? Is coverage adequate?
✅ Performance: Any performance implications?
✅ Documentation: Are changes documented?
✅ Kubernetes Integration: Correct K8s patterns if applicable
✅ MCP Server Implementation: Proper MCP patterns if applicable

CRITICAL RULES:
- ONLY work with repository: fuzzylabs/sre-agent (owner="fuzzylabs", repo="sre-agent")
- Use correct parameter names: owner, repo, pullNumber, method (not pull_number!)
- ALWAYS get the diff with method="get_diff" - don't just review metadata
- Provide specific, actionable feedback on the actual code changes
- Highlight both strengths and areas for improvement

OUTPUT FORMAT:
Provide a clear, structured review with sections for each focus area that's relevant to the PR."""

result = pr_review_agent.run_sync('Review the pull request titled "Add Ollama provider support for local LLM inference"')
print(result.output)
