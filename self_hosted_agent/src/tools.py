"""Tools and MCP server configuration for the PR review agent."""

from pydantic_ai import RunContext, ToolDefinition
from pydantic_ai.mcp import MCPServerStreamableHTTP
import os

from config import get_config

cfg = get_config()

async def filter_github_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition]:
    """Only allow tools needed for PR review."""
    allowed_tools = {
        'search_pull_requests',       # Search PRs by title
        'pull_request_read',          # Get PR details with different methods
        'pull_request_review_write',  # Write operations on pull request reviews
    }
    return [tool_def for tool_def in tool_defs if tool_def.name in allowed_tools]


# GitHub MCP server
github_server = MCPServerStreamableHTTP(
    'https://api.githubcopilot.com/mcp/',
    headers={'Authorization': f'Bearer {cfg.github.token}'}
)

