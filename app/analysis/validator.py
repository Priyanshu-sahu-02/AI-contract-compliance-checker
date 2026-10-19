
def validate_result(
    policy_id: str,
    result: dict,
    retrieved_chunks: list[dict],
) -> dict:
    """
    Safety checks for the current sample policies.
    This is a prototype, not a universal legal validator.
    """

    contract_text = "\n".join(
        chunk.get("chunk_text", "")
        for chunk in retrieved_chunks
    ).casefold()

    result = result.copy()

    if policy_id == "POL-001":
        # "Without undue delay" does not prove a 24-hour deadline.
        if "24 hours" not in contract_text:
            if result["status"] == "Compliant":
                result["status"] = "Needs review"
            result["explanation"] += (
                " Validation: the retrieved text does not explicitly "
                "confirm a 24-hour deadline."
            )

    elif policy_id == "POL-002":
        # Both encryption requirements must be explicitly supported.
        has_at_rest = "at rest" in contract_text
        has_in_transit = "in transit" in contract_text

        if not (has_at_rest and has_in_transit):
            if result["status"] == "Compliant":
                result["status"] = "Needs review"
            result["explanation"] += (
                " Validation: retrieved evidence does not explicitly "
                "confirm both encryption at rest and in transit."
            )

    elif policy_id == "POL-003":
        # A breach cure period is not automatically a termination notice.
        if result["status"] == "Compliant":
            result["status"] = "Needs review"
            result["explanation"] += (
                " Validation: distinguish end-of-term notice from "
                "early termination and a breach cure period."
            )

    # Verify that evidence is present in the retrieved text.
    evidence = result.get("evidence", "").strip()

    if evidence and not evidence.startswith("No relevant quotation"):
        # Remove common citation suffixes before checking the quotation.
        quote = evidence.split(" (Section", 1)[0].strip()
        if quote.casefold() not in contract_text:
            result["status"] = "Needs review"
            result["explanation"] += (
                " Validation: the evidence quotation could not be "
                "verified against the retrieved contract text."
            )
            result["recommendation"] = (
                "Verify the evidence against the original contract "
                "before making a compliance decision."
            )

    return result
