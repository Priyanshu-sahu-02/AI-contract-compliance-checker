
from app.rag.retriever import search_similar_chunks

results = search_similar_chunks(
    query="What does the contract say about data breaches?",
    document_name="sample_contract_compliance_test.pdf",
    k=3,
)

for i, result in enumerate(results, start=1):
    print(f"\n--- Result {i} ---")
    print("Document:", result["document_name"])
    print("Distance:", round(result["distance"], 4))
    print("Clause:", result["chunk_text"])
