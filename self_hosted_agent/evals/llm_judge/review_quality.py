"""Evaluate PR review quality using real git diffs."""

from typing import Any
from dataclasses import dataclass
import os
from pydantic_evals import Dataset
from pydantic_evals.evaluators import LLMJudge
from pydantic_ai import RunContext, ToolsetTool, WrapperToolset

from agent import pr_review_agent
from test_cases import TEST_CASES

from pydantic_ai.mcp import MCPServerStreamableHTTP

import mlflow
from config import get_config
from prompt import PROMPT_VERSION

LLM_JUDGE_MODEL = 'anthropic:claude-sonnet-4-5'

@dataclass
class MockToolsetWithDiff(WrapperToolset):
    """Mock toolset that returns predefined diffs for each test case."""
    
    test_case_metadata: dict[str, Any] | None = None
    
    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext,
        tool: ToolsetTool,
    ) -> Any:
        """Return mock data with test case specific diffs."""
        
        if not self.test_case_metadata:
            return {"mocked": True, "tool": name}
        
        pr_number = self.test_case_metadata.get('pr_number', 85)
        
        if name == 'search_pull_requests':
            return {
                "items": [{
                    "number": pr_number,
                    "title": self.test_case_metadata.get('title', 'Test PR'),
                    "state": "open",
                    "user": {"login": "developer"}
                }]
            }
        
        elif name == 'pull_request_read':
            method = tool_args.get('method', 'get')
            
            if method == 'get':
                return {
                    "number": pr_number,
                    "title": self.test_case_metadata.get('title', 'Test PR'),
                    "state": "open",
                    "body": f"PR to {self.test_case_metadata.get('title', 'make changes')}",
                    "user": {"login": "developer"}
                }
            elif method == 'get_diff':
                return self.test_case_metadata.get('diff', '# No diff available')
            elif method == 'get_files':
                # Extract files from diff
                return [{"filename": "test.py", "status": "modified"}]
            else:
                return {"number": pr_number}
        
        elif name == 'pull_request_review_write':
            return {
                "id": 12345,
                "state": "COMMENTED",
                "submitted_at": "2024-01-01T00:00:00Z",
                "body": tool_args.get('body', 'Review submitted')
            }
        
        return {"mocked": True, "tool": name, "args": tool_args}


INPUTS_TO_METADATA = {case.inputs: case.metadata for case in TEST_CASES}


def run_review_with_diff(inputs: str) -> str:
    """Run agent with a specific test case's diff.
    
    This task function is called by pydantic-evals with just the inputs string.
    We look up the metadata from our mapping.
    """
    metadata = INPUTS_TO_METADATA.get(inputs, {})
    
    # Create a fresh MCP server for this event loop (avoids event loop conflicts)
    fresh_github_server = MCPServerStreamableHTTP(
        'https://api.githubcopilot.com/mcp/',
        headers={'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}
    )
    
    # Wrap it with our mock that intercepts tool responses
    mock_toolset = MockToolsetWithDiff(
        wrapped=fresh_github_server,
        test_case_metadata=metadata
    )
    
    with pr_review_agent.override(toolsets=[mock_toolset]):
        result = pr_review_agent.run_sync(inputs)
        return result.output


# Dataset with evaluators
dataset = Dataset(
    cases=TEST_CASES,
    evaluators=[
        # LLM Judge for overall quality
        LLMJudge(
            rubric="""Score the PR review from 0-1 based on:
            - Actionability: Does it give specific, implementable suggestions?
            - Completeness: Does it identify the key issues in the code?
            - Technical accuracy: Are the concerns valid and correct?
            - Clarity: Is the feedback clear and well-structured?
            - Professionalism: Is the tone constructive?
            
            Return 1.0 for excellent, 0.7 for good, 0.5 for acceptable, 0.3 for poor.""",
            score={'evaluation_name': 'ReviewQuality', 'include_reason': True},
            model=LLM_JUDGE_MODEL,
        ),
        
        # Specific rubric for security awareness
        LLMJudge(
            rubric="""Does the review identify security issues if present?
            Check if the review mentions:
            - SQL injection vulnerabilities
            - Plaintext password handling
            - Input validation issues
            
            Return 1.0 if security issues are caught, 0.0 if missed.""",
            score={'evaluation_name': 'SecurityAwareness', 'include_reason': True},
            model=LLM_JUDGE_MODEL,
        ),
        
        # Check for test coverage feedback
        LLMJudge(
            rubric="""Does the review mention test coverage appropriately?
            - Flags missing tests for new code
            - Acknowledges good test coverage when present
            - Suggests specific test scenarios
            
            Return 1.0 for good test awareness, 0.5 for partial, 0.0 for none.""",
            score={'evaluation_name': 'TestAwareness', 'include_reason': True},
            model=LLM_JUDGE_MODEL,
        ),
    ]
)


if __name__ == '__main__':
    # Get current config
    cfg = get_config()

    # Start MLflow experiment
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("pr-review-agent-system-prompt")
    
    # Run evaluation
    print("Running evaluation...")
    report = dataset.evaluate_sync(run_review_with_diff)
    
    with mlflow.start_run(run_name=f"prompt_version_{PROMPT_VERSION}"):
        # Log parameters
        mlflow.log_param("model_provider", cfg.model.provider)
        mlflow.log_param("model_name", getattr(cfg.model, cfg.model.provider).model_name)
        mlflow.log_param("prompt_name", cfg.mlflow.prompt_name)
        mlflow.log_param("prompt_version", PROMPT_VERSION)
        mlflow.log_param("llm_judge_model", LLM_JUDGE_MODEL)
        
        # Extract and log metrics from report
        for case_result in report.cases:
            case_id = case_result.name
            
            # Log evaluation scores
            for score_name, eval_result in case_result.scores.items():
                metric_name = f"{case_id}_{score_name}"
                mlflow.log_metric(metric_name, eval_result.value)
                
            # Log case duration
            if case_result.task_duration:
                mlflow.log_metric(f"{case_id}_duration_seconds", case_result.task_duration)
        
        # Calculate and log average scores per evaluation type
        eval_scores = {}
        for case_result in report.cases:
            for score_name, eval_result in case_result.scores.items():
                if score_name not in eval_scores:
                    eval_scores[score_name] = []
                eval_scores[score_name].append(eval_result.value)
        
        for eval_name, scores in eval_scores.items():
            avg_score = sum(scores) / len(scores)
            mlflow.log_metric(f"avg_{eval_name}", avg_score)
        
        # Log overall pass rate
        total_scores = sum(len(c.scores) for c in report.cases)
        passed_scores = sum(1 for c in report.cases for eval_result in c.scores.values() if eval_result.value >= 0.7)
        pass_rate = passed_scores / total_scores if total_scores > 0 else 0
        mlflow.log_metric("pass_rate", pass_rate)
        
        print(f"\nLogged to MLflow run: {mlflow.active_run().info.run_id}")
        print("\nAverage scores:")
        for eval_name, scores in eval_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            print(f"  {eval_name}: {avg:.2f}")
        print(f"  Pass rate (>=0.7): {pass_rate:.1%}")
    
    # Print detailed report
    print("\n" + "="*80)
    report.print(include_input=False, include_output=True, include_durations=True)