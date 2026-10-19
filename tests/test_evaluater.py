
from app.rag.retriever import search_similar_chunks
from app.analysis.evaluator import evaluate_policy


document_name = "sample_contract_compliance_test.pdf"

policy = (
    "The provider must notify the customer of a confirmed "
    "personal-data breach within 24 hours."
)

print("Searching contract evidence...")

chunks = search_similar_chunks(
    query=(
        "personal data breach notification deadline "
        "how quickly must the provider notify the customer"
    ),
    document_name=document_name,
    k=3,
)

print("Evaluating policy with Ollama...")

result = evaluate_policy(
    policy=policy,
    retrieved_chunks=chunks,
    document_name=document_name,
)

print("\n--- COMPLIANCE RESULT ---")
for key, value in result.items():
    print(f"\n{key.upper()}:\n{value}")
