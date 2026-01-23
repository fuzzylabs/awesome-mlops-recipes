"""Verify that tools are called in the correct sequence."""

from dataclasses import dataclass

from common import STANDARD_CASES, run_agent_with_mock_tools
from pydantic_evals import Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ToolOrderEvaluator(Evaluator):  # type: ignore[misc]
    """Check if tools were called in the expected order."""

    expected_order: list[str]

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | str]:
        """Check tool call order from the span tree.

        Args:
            ctx: Evaluator context containing spans.

        Returns:
            dict[str, bool | str]: Evaluation results with order details.
        """
        # Collect all tool calls with their timestamps
        tool_calls = []

        if hasattr(ctx, "span_tree") and ctx.span_tree:
            for root in ctx.span_tree.roots:
                for node in [root] + root.descendants:
                    if node.name == "running tool":
                        tool_name = node.attributes.get("gen_ai.tool.name")
                        if tool_name:
                            tool_calls.append(
                                {"name": tool_name, "timestamp": node.start_timestamp}
                            )

        # Sort by timestamp
        tool_calls.sort(key=lambda x: x["timestamp"])
        actual_order = [t["name"] for t in tool_calls]

        # Check if order follows expected progression
        # (allows repeats, but no backwards steps)
        order_correct = True
        last_expected_idx = -1

        for tool in actual_order:
            if tool in self.expected_order:
                expected_idx = self.expected_order.index(tool)
                if expected_idx < last_expected_idx:
                    order_correct = False
                    break
                last_expected_idx = expected_idx

        return {
            "order_correct": order_correct,
            "actual_order": str(actual_order),
            "expected_order": str(self.expected_order),
        }


# Dataset with order checking
dataset = Dataset(
    cases=STANDARD_CASES,
    evaluators=[
        ToolOrderEvaluator(
            expected_order=[
                "search_pull_requests",
                "pull_request_read",
                "pull_request_review_write",
            ]
        )
    ],
)


if __name__ == "__main__":
    print("📋 Verifying tool call order...")
    print("Expected: search → read → review (repeats allowed)\n")

    report = dataset.evaluate_sync(run_agent_with_mock_tools)

    print("\n" + "=" * 70)
    report.print(include_input=False, include_output=False, include_durations=True)
    print("=" * 70)
