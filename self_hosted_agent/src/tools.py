"""Tools and MCP server configuration for the PR review agent."""

from config import get_config
from pydantic_ai import RunContext, ToolDefinition
from pydantic_ai.mcp import MCPServerStreamableHTTP

cfg = get_config()


def _build_mcp_headers() -> dict[str, str]:
    """Build headers for the MCP gateway or direct GitHub MCP.

    Returns:
        dict[str, str]: HTTP headers for MCP requests.
    """
    headers: dict[str, str] = {}
    if cfg.mcp.gateway_url:
        if cfg.mcp.gateway_auth_token:
            headers["Authorization"] = f"Bearer {cfg.mcp.gateway_auth_token}"
        if cfg.mcp.gateway_forward_github_token:
            if not cfg.github.token:
                raise ValueError("GITHUB_TOKEN must be set when forwarding upstream auth")
            headers["X-Upstream-Authorization"] = f"Bearer {cfg.github.token}"
    else:
        if not cfg.github.token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        headers["Authorization"] = f"Bearer {cfg.github.token}"
    return headers


async def filter_github_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition]:
    """Filter tool definitions down to PR review needs.

    Args:
        ctx: Run context for the agent.
        tool_defs: Available tool definitions.

    Returns:
        list[ToolDefinition]: Filtered list of tool definitions.
    """
    allowed_tools = {
        "search_pull_requests",  # Search PRs by title
        "pull_request_read",  # Get PR details with different methods
        "pull_request_review_write",  # Write operations on pull request reviews
    }
    return [tool_def for tool_def in tool_defs if tool_def.name in allowed_tools]


# GitHub MCP server
github_server = MCPServerStreamableHTTP(
    cfg.mcp.gateway_url or cfg.mcp.github_mcp_url,
    headers=_build_mcp_headers(),
)
