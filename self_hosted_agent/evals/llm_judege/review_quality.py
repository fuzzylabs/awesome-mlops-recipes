from pydantic_evals.evaluators import LLMJudge, Contains, IsInstance

evaluators = [
    # Basic checks
    IsInstance(type_name='str'),
    Contains(value='PR', case_sensitive=False),
    
    # LLM-as-a-Judge for quality
    LLMJudge(
        rubric="""Score the PR review from 0-1 based on:
        - Actionability: Does it give specific suggestions?
        - Completeness: Does it cover code quality, security, tests?
        - Clarity: Is the feedback clear and constructive?
        - Professionalism: Is the tone appropriate?
        
        Return 1.0 for excellent, 0.5 for acceptable, 0.0 for poor.""",
        score={'evaluation_name': 'ReviewQuality', 'include_reason': True}
    ),
]