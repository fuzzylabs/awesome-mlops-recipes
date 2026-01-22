"""Runtime guardrails for the RAG API."""


import re

from guardrails import Guard
from guardrails.validators import FailResult, PassResult, Validator, register_validator


FINANCIAL_ADVICE_REFUSAL = (
    "I cannot provide financial advice or investment recommendations. "
    "I am not a financial advisor."
)

_FINANCIAL_ADVICE_PATTERNS = [
    re.compile(r"\bshould i\b", re.IGNORECASE),
    re.compile(r"\bshould we\b", re.IGNORECASE),
    re.compile(r"\bis it (a )?good time to\b", re.IGNORECASE),
    re.compile(r"\bdo you recommend\b", re.IGNORECASE),
    re.compile(r"\bwould you recommend\b", re.IGNORECASE),
    re.compile(r"\b(can|should) i (buy|sell|invest)\b", re.IGNORECASE),
    re.compile(r"\b(can|should) we (buy|sell|invest)\b", re.IGNORECASE),
    re.compile(r"\b(my|our) portfolio\b", re.IGNORECASE),
    re.compile(r"\bprice target\b", re.IGNORECASE),
]


def is_financial_advice_request(question: str) -> bool:
    """Return True when the question looks like a request for financial advice."""
    normalized = question.strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in _FINANCIAL_ADVICE_PATTERNS)


def _is_financial_advice_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return (
        "financial advice" in lowered
        or "not a financial advisor" in lowered
        or "cannot provide" in lowered
    )


@register_validator(name="financial_advice_refusal", data_type="string")
class FinancialAdviceRefusalValidator(Validator):
    """Validate that the model refuses financial advice requests."""

    def _validate(self, value: str, metadata: dict) -> PassResult | FailResult:
        must_refuse = bool(metadata.get("must_refuse", False))
        if not must_refuse:
            return PassResult()
        if _is_financial_advice_refusal(value):
            return PassResult()
        return FailResult("Expected financial advice refusal but model answered.")


_FINANCIAL_ADVICE_GUARD = Guard().use(FinancialAdviceRefusalValidator)


def apply_financial_advice_guardrail(question: str, answer: str) -> tuple[str, bool]:
    """Return a refusal response when financial advice must be blocked."""
    if not is_financial_advice_request(question):
        return answer, False
    outcome = _FINANCIAL_ADVICE_GUARD.validate(answer, metadata={"must_refuse": True})
    if outcome.validation_passed:
        return answer, False
    return FINANCIAL_ADVICE_REFUSAL, True
