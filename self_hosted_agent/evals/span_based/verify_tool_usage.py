"""Verify that the agent uses the correct tools."""

from common import STANDARD_CASES, run_agent_with_mock_tools
from pydantic_evals import Dataset
from pydantic_evals.evaluators import HasMatchingSpan

# Evaluators: Check that each required tool is called
dataset = Dataset(
    cases=STANDARD_CASES,
    evaluators=[
        HasMatchingSpan(
            query={
                "name_equals": "running tool",
                "has_attributes": {"gen_ai.tool.name": "search_pull_requests"},
            },
            evaluation_name="UsesSearchTool",
        ),
        HasMatchingSpan(
            query={
                "name_equals": "running tool",
                "has_attributes": {"gen_ai.tool.name": "pull_request_read"},
            },
            evaluation_name="UsesReadTool",
        ),
        HasMatchingSpan(
            query={
                "name_equals": "running tool",
                "has_attributes": {"gen_ai.tool.name": "pull_request_review_write"},
            },
            evaluation_name="UsesReviewTool",
        ),
    ],
)


if __name__ == "__main__":
    print("🔧 Verifying tool usage...")
    print("Checks: search → read → review tools are called\n")

    report = dataset.evaluate_sync(run_agent_with_mock_tools)

    print("\n" + "=" * 70)
    report.print(include_input=False, include_output=False, include_durations=True)
    print("=" * 70)
