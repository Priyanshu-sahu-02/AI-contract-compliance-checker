
import json
from app.graph.workflow import run_compliance_check

report = run_compliance_check(
    "sample_contract_compliance_test.pdf"
)

print(json.dumps(report, indent=2, ensure_ascii=False))
