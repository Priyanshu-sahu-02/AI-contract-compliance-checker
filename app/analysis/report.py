
from app.policy import ORGANIZATION_POLICIES
from app.rag.retriever import search_similar_chunks
from app.analysis.evaluator import evaluate_policy
from app.analysis.validator import validate_result


def generate_compliance_report(document_name: str) -> dict:
    results = []

    for policy_item in ORGANIZATION_POLICIES:
        print(f"Checking: {policy_item['name']}")

        chunks = search_similar_chunks(
            query=policy_item["policy"],
            document_name=document_name,
            k=5,
        )

        result = evaluate_policy(
            policy=policy_item["policy"],
            retrieved_chunks=chunks,
            document_name=document_name,
        )

        result = validate_result(
            policy_id=policy_item["id"],
            result=result,
            retrieved_chunks=chunks,
        )

        results.append({
            "policy_id": policy_item["id"],
            "policy_name": policy_item["name"],
            "status": result["status"],
            "explanation": result["explanation"],
            "evidence": result["evidence"],
            "recommendation": result["recommendation"],
        })

    summary = {
        "Compliant": 0,
        "Non-compliant": 0,
        "Missing": 0,
        "Needs review": 0,
    }

    for result in results:
        status = result["status"]
        if status in summary:
            summary[status] += 1

    return {
        "document_name": document_name,
        "total_policies": len(results),
        "summary": summary,
        "results": results,
    }
