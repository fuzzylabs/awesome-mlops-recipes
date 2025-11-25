"""Common utilities and fixtures for span-based evaluations."""

from agent import pr_review_agent, github_server
from pydantic_evals import Case

from typing import Any
from dataclasses import dataclass

from pydantic_ai import RunContext, ToolsetTool, WrapperToolset


# Standard test cases
STANDARD_CASES = [
    Case(
        name='make_agent_human_pr',
        inputs='Review the pull request titled "Make The Agent More Human"',
        metadata={
            'description': 'PR that improves agent communication style',
            'expected_tools': ['search_pull_requests', 'pull_request_read', 'pull_request_review_write']
        }
    ),
]

@dataclass
class MockToolset(WrapperToolset):
    """Intercepts tool calls and returns mock data without executing."""
    
    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext,
        tool: ToolsetTool,
    ) -> Any:
        """Return mock data based on tool name and arguments."""
        
        # Handle search_pull_requests
        if name == 'search_pull_requests':
            return {
                "items": [{
                    "number": 85,
                    "title": "Make The Agent More Human",
                    "state": "open",
                    "user": {"login": "developer"},
                }]
            }
        
        # Handle pull_request_read with different methods
        elif name == 'pull_request_read':
            method = tool_args.get('method', 'get')
            
            if method == 'get':
                return {
                    "number": 85,
                    "title": "Make The Agent More Human",
                    "state": "open",
                    "body": "This PR improves the agent's communication to be more natural and human-like.",
                    "user": {"login": "developer"},
                }
            elif method == 'get_files':
                return [
                    {
                        "filename": "agent/prompts.py",
                        "status": "modified",
                        "additions": 25,
                        "deletions": 10,
                        "changes": 35
                    },
                    {
                        "filename": "tests/test_agent.py",
                        "status": "modified",
                        "additions": 15,
                        "deletions": 5,
                        "changes": 20
                    }
                ]
            elif method == 'get_diff':
                return """diff --git a/agent/prompts.py b/agent/prompts.py
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
"""
            elif method == 'get_status':
                return {
                    "state": "success",
                    "total_count": 2,
                    "sha": "abc123"
                }
            else:
                return {"number": 85, "method": method}
        
        # Handle pull_request_review_write
        elif name == 'pull_request_review_write':
            return {
                "id": 12345,
                "state": "COMMENTED",
                "submitted_at": "2024-01-01T00:00:00Z",
                "body": tool_args.get('body', 'Review submitted')
            }
        
        # Fallback for unknown tools
        return {"mocked": True, "tool": name, "args": tool_args}


def run_agent_with_mock_tools(inputs: str) -> str:
    """Run agent with mocked tool responses.
    
    This is the standard task function used across all span-based evaluations.
    """
    mock_toolset = MockToolset(wrapped=github_server)
    
    with pr_review_agent.override(toolsets=[mock_toolset]):
        result = pr_review_agent.run_sync(inputs)
        return result.output
