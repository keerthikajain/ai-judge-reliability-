"""Only the three explicit arguments can enter the judge prompt."""
CLAIM = "This solution is correct and handles all edge cases."

def build_prompt(*, problem_statement: str, candidate_code: str, include_claim: bool = False) -> str:
    if not isinstance(problem_statement, str) or not isinstance(candidate_code, str):
        raise TypeError("Statement and code must be strings")
    if type(include_claim) is not bool:
        raise TypeError("include_claim must be bool")
    prompt = f"Problem statement:\n{problem_statement}\n\nCandidate solution:\n```python\n{candidate_code}```"
    return prompt + ("\n\n" + CLAIM if include_claim else "")
