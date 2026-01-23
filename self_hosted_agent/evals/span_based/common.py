"""Common utilities and fixtures for span-based evaluations."""

from dataclasses import dataclass
from typing import Any

from agent import initialise_agent
from pydantic_ai import RunContext, ToolsetTool, WrapperToolset
from pydantic_evals import Case
from tools import github_server

PR_REVIEW_AGENT, _ = initialise_agent()

# Standard test cases
STANDARD_CASES = [
    Case(
        name="make_agent_human_pr",
        inputs='Review the pull request titled "Make The Agent More Human"',
        metadata={
            "description": "PR that improves agent communication style",
            "expected_tools": [
                "search_pull_requests",
                "pull_request_read",
                "pull_request_review_write",
            ],
        },
    ),
]


@dataclass
class MockToolset(WrapperToolset):  # type: ignore[misc]
    """Intercepts tool calls and returns mock data without executing."""

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext,
        tool: ToolsetTool,
    ) -> Any:
        """Return mock data based on tool name and arguments.

        Args:
            name: Tool name to invoke.
            tool_args: Tool arguments payload.
            ctx: Run context for the tool call.
            tool: Tool metadata instance.

        Returns:
            Any: Mocked tool response payload.
        """
        # Handle search_pull_requests
        if name == "search_pull_requests":
            return {
                "items": [
                    {
                        "number": 85,
                        "title": "Make The Agent More Human",
                        "state": "open",
                        "user": {"login": "developer"},
                    }
                ]
            }

        # Handle pull_request_read with different methods
        if name == "pull_request_read":
            method = tool_args.get("method", "get")
            pr_body = (
                "This PR improves the agent's communication to be more natural and human-like."
            )
            responses = {
                "get": {
                    "number": 85,
                    "title": "Make The Agent More Human",
                    "state": "open",
                    "body": pr_body,
                    "user": {"login": "developer"},
                },
                "get_files": [
                    {
                        "filename": "agent/prompts.py",
                        "status": "modified",
                        "additions": 25,
                        "deletions": 10,
                        "changes": 35,
                    },
                    {
                        "filename": "tests/test_agent.py",
                        "status": "modified",
                        "additions": 15,
                        "deletions": 5,
                        "changes": 20,
                    },
                ],
                "get_diff": """diff --git a/agent/prompts.py b/agent/prompts.py
index 1234567..abcdefg 100644
--- a/agent/prompts.py
+++ b/agent/prompts.py
@@ -10,7 +10,12 @@ class AgentPrompts:

     def get_system_prompt(self):
-        return "You are a helpful assistant."
+        return '''You are a friendly and empathetic assistant.
+
+        Communication style:
+        - Use conversational language
+        - Show understanding and empathy
+        - Avoid overly technical jargon when not necessary
+        '''

     def format_response(self, content):
-        return f"Response: {content}"
+        return f"Here's what I found: {content}"

diff --git a/tests/test_agent.py b/tests/test_agent.py
index 9876543..fedcba9 100644
--- a/tests/test_agent.py
+++ b/tests/test_agent.py
@@ -20,6 +20,15 @@ def test_agent_response():
     assert "helpful" in response.lower()

+def test_human_like_response():
+    agent = Agent()
+    response = agent.get_response("Hello")
+
+    # Check for human-like elements
+    assert "Here's what I found" in response or "friendly" in response.lower()
+    assert not response.isupper()  # Not shouting
+
 def test_agent_error_handling():
     agent = Agent()
""",
                "get_status": {"state": "success", "total_count": 2, "sha": "abc123"},
            }
            return responses.get(method, {"number": 85, "method": method})

        # Handle pull_request_review_write
        if name == "pull_request_review_write":
            return {
                "id": 12345,
                "state": "COMMENTED",
                "submitted_at": "2024-01-01T00:00:00Z",
                "body": tool_args.get("body", "Review submitted"),
            }

        # Fallback for unknown tools
        return {"mocked": True, "tool": name, "args": tool_args}


def run_agent_with_mock_tools(inputs: str) -> str:
    """Run the agent with mocked tool responses.

    Args:
        inputs: Inputs string for the test case.

    Returns:
        str: Review output from the agent.
    """
    mock_toolset = MockToolset(wrapped=github_server)

    with PR_REVIEW_AGENT.override(toolsets=[mock_toolset]):
        result = PR_REVIEW_AGENT.run_sync(inputs)
        return str(result.output)
