
import csv
import io
import json

import requests
import streamlit as st

st.set_page_config(
    page_title="Contract Compliance | AI Review",
    page_icon="📄",
    layout="wide",
)

API_URL = "http://127.0.0.1:8000/check-contract"

STATUS_OPTIONS = [
    "All",
    "Compliant",
    "Non-compliant",
    "Missing",
    "Needs review",
]


def count_status(results, status):
    return sum(
        1 for item in results
        if item.get("status") == status
    )


def make_csv(results):
    output = io.StringIO()
    fields = [
        "policy_id",
        "policy_name",
        "status",
        "evidence",
        "explanation",
        "recommendation",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fields,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(results)

    return output.getvalue().encode("utf-8-sig")


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("📄 Contract Review")
    st.caption("AI-assisted compliance workspace")
    st.divider()

    st.markdown("### How it works")
    st.write("1. Upload a contract PDF")
    st.write("2. Run policy analysis")
    st.write("3. Review evidence and findings")
    st.write("4. Export the report")

    st.divider()
    st.caption(
        "AI results are preliminary. "
        "Verify evidence before making decisions."
    )


# ---------------- MAIN HEADER ----------------

st.title("Contract Compliance Checker")
st.write(
    "Compare a third-party contract against "
    "your organization's policies."
)

uploaded_file = st.file_uploader(
    "Choose a contract PDF",
    type=["pdf"],
    help="Upload a text-readable PDF contract.",
)

if uploaded_file:
    st.success(f"Selected: {uploaded_file.name}")

    if st.button(
        "Run Compliance Analysis",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Extracting evidence and evaluating policies..."
            ):
                response = requests.post(
                    API_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=600,
                )

            if response.ok:
                st.session_state["compliance_report"] = (
                    response.json()
                )
                st.session_state["report_filename"] = (
                    uploaded_file.name
                )
                st.success("Analysis completed.")
            else:
                st.error(
                    f"Backend error: HTTP {response.status_code}"
                )
                st.code(response.text[:3000])

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to FastAPI. Start the backend first."
            )
        except requests.exceptions.Timeout:
            st.error(
                "The request timed out. Check the backend terminal "
                "before retrying."
            )
        except requests.exceptions.RequestException as exc:
            st.error(f"Request failed: {exc}")
        except ValueError:
            st.error("The backend returned invalid JSON.")

# Show whether this report was generated fresh or loaded from cache.
report = st.session_state.get("compliance_report")

if report:
    if report.get("cache_hit", False):
        st.success(
            "⚡ Cached Report — Loaded from database. "
            "PDF extraction and AI evaluation were skipped."
        )
    else:
        st.info(
            "🆕 Fresh Report — Contract was processed and "
            "AI compliance evaluation was performed."
        )

if report:
    results = report.get("results", [])
    summary = report.get("summary", {})

    st.divider()

    st.subheader("Analysis Overview")
    st.caption(
        f"Document: {report.get('document_name', 'Unknown')} "
        f"· Policies checked: {report.get('total_policies', len(results))}"
    )

    # Summary cards use actual backend counts.
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Compliant",
        summary.get("Compliant", count_status(results, "Compliant")),
    )
    c2.metric(
        "Needs review",
        summary.get(
            "Needs review",
            count_status(results, "Needs review"),
        ),
    )
    c3.metric(
        "Non-compliant",
        summary.get(
            "Non-compliant",
            count_status(results, "Non-compliant"),
        ),
    )
    c4.metric(
        "Missing",
        summary.get("Missing", count_status(results, "Missing")),
    )

    st.warning(
        "Preliminary AI assessment only. A status is not a legal "
        "conclusion, and retrieved evidence may be incomplete."
    )

    # Download options
    d1, d2, _ = st.columns([1, 1, 2])

    with d1:
        st.download_button(
            "Download JSON",
            data=json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            ),
            file_name="compliance_report.json",
            mime="application/json",
            use_container_width=True,
        )

    with d2:
        st.download_button(
            "Download CSV",
            data=make_csv(results),
            file_name="compliance_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    st.subheader("Policy Findings")

    f1, f2 = st.columns([2, 1])

    with f1:
        search = st.text_input(
            "Search policies",
            placeholder="Search by name, ID, evidence...",
        )

    with f2:
        selected_status = st.selectbox(
            "Filter by status",
            STATUS_OPTIONS,
        )

    filtered_results = []

    for item in results:
        status = item.get("status", "Unknown")

        if (
            selected_status != "All"
            and status != selected_status
        ):
            continue

        searchable_text = " ".join([
            str(item.get("policy_id", "")),
            str(item.get("policy_name", "")),
            str(item.get("evidence", "")),
            str(item.get("explanation", "")),
        ]).casefold()

        if search.casefold() not in searchable_text:
            continue

        filtered_results.append(item)

    st.caption(f"Showing {len(filtered_results)} policy findings")

    if not filtered_results:
        st.info("No policies match the selected filters.")

    for item in filtered_results:
        policy_id = item.get("policy_id", "")
        policy_name = item.get("policy_name", "Unnamed policy")
        status = item.get("status", "Unknown")

        with st.expander(
            f"{policy_id} · {policy_name} — {status}",
            expanded=(status in ["Needs review", "Non-compliant"]),
        ):
            st.markdown(f"**Status:** {status}")

            st.markdown("**Explanation**")
            st.write(
                item.get("explanation") or "No explanation provided."
            )

            st.markdown("**Contract evidence**")
            st.write(
                item.get("evidence") or "No evidence provided."
            )

            st.markdown("**Recommended action**")
            st.write(
                item.get("recommendation")
                or "No recommendation provided."
            )

    with st.expander("View complete API response"):
        st.json(report)
