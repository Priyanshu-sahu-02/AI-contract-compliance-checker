
import json
from app.analysis.report import generate_compliance_report

report = generate_compliance_report(
    document_name="sample_contract_compliance_test.pdf"
)

print("\n=== CONTRACT COMPLIANCE REPORT ===")
print("Document:", report["document_name"])
print("Total Policies:", report["total_policies"])

print("\n=== SUMMARY ===")
for status, count in report["summary"].items():
    print(f"{status}: {count}")

print("\n=== POLICY RESULTS ===")
for item in report["results"]:
    print(f"\n{item['policy_id']} - {item['policy_name']}")
    print("Status:", item["status"])
    print("Explanation:", item["explanation"])
    print("Evidence:", item["evidence"])
    print("Recommendation:", item["recommendation"])
