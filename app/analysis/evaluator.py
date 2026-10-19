from typing import Literal

from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama

from app.analysis.prompts import EVALUATION_PROMPT

compliance_status = Literal[
    "Compliant",
    "Non-compliant",
    "Missing",
    "Needs review"
]

class ComplianceResult(BaseModel):
    status: compliance_status = Field( description="Compliance status based on supplied evidence")
    explanation: str = Field( description="Why the evidence does or does not satisfy the policy")
    evidence: str = Field( description="Short exact quote from the supplied contract evidence, or state that evidence is insufficient")
    recommendation: str = Field(description="Suggested follow-up action, without giving a final legal decision")

def get_llm():
    return ChatOllama(
        model = "llama3.2:3b",
        temperature = 0
    )

def evaluate_policy(
        policy: str,
        retrieved_chunks: list[dict],
        document_name: str = "unknown document",
)-> dict:
    if not policy.strip():
        raise ValueError("Policy cannot be empty.")

    if not retrieved_chunks:
        return ComplianceResult(
            status="Needs review",
            explanation=(
                "No contract evidence was retrieved. "
                "Compliance cannot be determined."
            ),
            evidence="No evidence available.",
            recommendation=(
                "Check document ingestion and search with a more specific query."
            ),
        ).model_dump()

    
    evidence = "\n\n".join(
    (
        f"Evidence {index}\n"
        f"Document: {item['document_name']}\n"
        f"Contract text:\n{item['chunk_text']}"
    )
    for index, item in enumerate(retrieved_chunks, start=1)
    )

    structured_llm = get_llm().with_structured_output(
        ComplianceResult
    )

    chain = EVALUATION_PROMPT | structured_llm

    result = chain.invoke(
        {
            "policy": policy,
            "document_name": document_name,
            "evidence": evidence,
        }
    )
    return result.model_dump()


