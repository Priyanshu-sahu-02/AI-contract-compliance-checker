from typing import TypedDict

class ComplianceState(TypedDict, total=False):
    document_name: str
    policy_index: int
    results: list[dict]
    current_policy: dict
    retrieved_chunks: list[dict]
    current_result: dict
    summary: dict
    error: str