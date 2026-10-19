from langgraph.graph import StateGraph, START, END

from app.graph.state import ComplianceState
from app.policy import ORGANIZATION_POLICIES
from app.rag.retriever import search_similar_chunks
from app.analysis.evaluator import evaluate_policy
from app.analysis.validator import validate_result

def retrieve_evidence(state: ComplianceState):
    policy = state["current_policy"]

    chunks = search_similar_chunks(
        query=policy["policy"],
        document_name=state["document_name"],
        k=5,
    )

    return {"retrieved_chunks": chunks}

def evaluate_current_policy(state: ComplianceState):
    policy = state["current_policy"]

    result = evaluate_policy(
        policy=policy["policy"],
        retrieved_chunks=state["retrieved_chunks"],
        document_name=state["document_name"],
    )

    result = validate_result(
        policy_id=policy["id"],
        result=result,
        retrieved_chunks=state["retrieved_chunks"],
    )

    return {"current_result": result}

def save_result_and_continue(state: ComplianceState):
    policy = state["current_policy"]
    result = state["current_result"]

    item = {
        "policy_id": policy["id"],
        "policy_name": policy["name"],
        **result,
    }

    results = state.get("results", []) + [item]
    next_index = state["policy_index"] + 1

    if next_index < len(ORGANIZATION_POLICIES):
        return {
            "results": results,
            "policy_index": next_index,
            "current_policy": ORGANIZATION_POLICIES[next_index],
        }

    summary = {
        status: sum(
            1 for r in results if r.get("status") == status
        )
        for status in [
            "Compliant",
            "Non-compliant",
            "Missing",
            "Needs review",
        ]
    }

    return {
        "results": results,
        "policy_index": next_index,
        "summary": summary,
    }

def should_continue(state: ComplianceState):
    if state.get("error"):
        return "end"

    if state["policy_index"] < len(ORGANIZATION_POLICIES):
        return "retrieve"

    return "end"

def build_workflow():
    graph = StateGraph(ComplianceState)

    graph.add_node("retrieve", retrieve_evidence)
    graph.add_node("evaluate", evaluate_current_policy)
    graph.add_node("save", save_result_and_continue)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_edge("evaluate", "save")

    graph.add_conditional_edges(
        "save",
        should_continue,
        {
            "retrieve": "retrieve",
            "end": END,
        },
    )

    return graph.compile()


compliance_graph = build_workflow()

def run_compliance_check(document_name: str) -> dict:
    if not ORGANIZATION_POLICIES:
        return {
            "document_name": document_name,
            "total_policies": 0,
            "summary": {},
            "results": [],
        }

    initial_state: ComplianceState = {
        "document_name": document_name,
        "policy_index": 0,
        "current_policy": ORGANIZATION_POLICIES[0],
        "results": [],
    }

    final_state = compliance_graph.invoke(initial_state)

    return {
        "document_name": document_name,
        "total_policies": len(final_state["results"]),
        "summary": final_state.get("summary", {}),
        "results": final_state["results"],
    }
