# AI Contract Compliance Checker

A portfolio project that analyzes a service-provider contract PDF against an organization's policy rules and produces an evidence-backed compliance report.

> **Important:** This tool provides preliminary review support, not legal advice. AI-generated classifications can be incorrect. A qualified human reviewer should verify cited clauses and conclusions before making legal or business decisions.

## Features

- PDF upload through a Streamlit dashboard.
- PDF text extraction and chunking.
- Local embeddings with `sentence-transformers/all-MiniLM-L6-v2`.
- PostgreSQL + `pgvector` similarity search.
- RAG-based contract evidence retrieval.
- Local policy evaluation with Ollama (`llama3.2:3b`).
- LangGraph workflow for policy-by-policy analysis.
- FastAPI backend and Streamlit dashboard.
- SHA-256 duplicate PDF detection.
- PostgreSQL JSONB report caching to avoid repeating evaluation for the same PDF.
- JSON and CSV report downloads.

## Technology Stack

Python · FastAPI · Streamlit · LangChain · LangGraph · Ollama · Sentence Transformers · PostgreSQL · pgvector · pypdf

## Architecture

```text
PDF Upload
   |
   v
FastAPI endpoint
   |
   v
PDF validation + size limit
   |
   v
SHA-256 content hash
   |
   +---- Existing completed report? ---- Yes ---> Return cached JSONB report
   |
   No
   |
   v
Extract text -> Chunk -> Generate embeddings
   |
   v
PostgreSQL + pgvector
   |
   v
LangGraph policy workflow
   |
   v
Retrieve evidence -> Ollama evaluation -> Validate results
   |
   v
Cache report in PostgreSQL JSONB
   |
   v
Streamlit dashboard: findings, filters, JSON/CSV export
```

## Example Policies

The current demonstration policy set in `app/policies.py` includes:

- **POL-001 — Data Breach Notification:** confirmed personal-data breaches must be reported within 24 hours.
- **POL-002 — Data Encryption:** customer data must be encrypted at rest and in transit.
- **POL-003 — Termination Notice:** at least 30 days' written notice before termination.

These are example policies for testing. Replace them with rules approved for your actual use case.

## Project Structure

```text
contract-compliance-checker/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── policies.py
│   ├── ingestion/
│   │   ├── parser.py
│   │   └── ingest.py
│   ├── rag/
│   │   ├── embeddings.py
│   │   └── retriever.py
│   ├── analysis/
│   │   ├── prompts.py
│   │   ├── evaluator.py
│   │   ├── validator.py
│   │   └── report.py
│   └── graph/
│       ├── state.py
│       └── workflow.py
├── ui/
│   └── dashboard.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Adjust the tree to match the actual files in your repository before publishing.

## Prerequisites

- Python compatible with `requirements.txt`
- PostgreSQL with `pgvector` installed
- Ollama installed and running
- Git (optional)

Pull the evaluator model:

```powershell
ollama pull llama3.2:3b
```

## Windows Setup

Run commands from the project root in PowerShell.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `.env` in the project root. Use the variable names expected by `app/database.py` and replace placeholders with your local PostgreSQL settings.

Example only:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=contract_compliance
DB_USER=your_postgres_user
DB_PASSWORD=your_password
```

Do not commit `.env`. Keep `.env.example` limited to placeholders.

### 4. Enable pgvector

In pgAdmin or `psql`, select the database used by the app and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Start the API

```powershell
uvicorn app.main:app --reload
```

API root: `http://127.0.0.1:8000/`  
Interactive API docs: `http://127.0.0.1:8000/docs`

### 6. Start the dashboard

Open a second PowerShell terminal, activate the virtual environment, navigate to the project root, and run:

```powershell
streamlit run ui/dashboard.py
```

Open the local URL shown by Streamlit.

## How to Use

1. Ensure PostgreSQL, pgvector, and Ollama are running.
2. Start FastAPI and Streamlit.
3. Upload a valid PDF contract in the dashboard.
4. Review policy status, explanation, evidence, and recommendations.
5. Download the report as JSON or CSV if needed.
6. Upload the exact same PDF again to verify report-cache reuse.

## API

### `GET /`

Checks whether the API is running.

### `POST /check-contract`

Uploads a PDF using multipart form data with a `file` field and returns a compliance report.

Example:

```bash
curl -X POST "http://127.0.0.1:8000/check-contract" \
  -F "file=@sample_contract.pdf"
```

Successful responses may include `document_reused` and `cache_hit` metadata. Confirm these fields and the configured upload limit in the current code before publishing.

## Duplicate Detection and Report Caching

- SHA-256 identifies identical PDF content regardless of its uploaded filename.
- A PostgreSQL document registry tracks the document hash, stored name, and processing status.
- Extracted chunks and embeddings are stored in `contract_chunks`.
- Completed reports are cached as PostgreSQL JSONB.
- Repeated uploads can reuse the cached report without repeating ingestion or LLM evaluation.

If policy definitions, prompts, models, or evaluation logic change, invalidate old cached reports or include a policy/evaluator version in the cache key.

## Final Testing Checklist

- [ ] Valid PDF generates a report.
- [ ] Re-uploading the same PDF returns a cached report.
- [ ] Invalid or corrupted PDF is rejected cleanly.
- [ ] Files exceeding the configured upload limit are rejected.
- [ ] Temporary files are deleted after success and failure.
- [ ] Database status and report cache remain consistent after failures.
- [ ] Evidence quotations match the original contract.
- [ ] Ambiguous policy wording is flagged for human review.
- [ ] `.env`, credentials, and real contracts are not tracked by Git.

Run the test suite if configured:

```powershell
pytest
```

Only document test commands and outcomes that actually work in your repository.

## Known Limitations

- LLMs can misinterpret legal wording or miss relevant clauses.
- Similarity retrieval may omit important evidence.
- Evidence validation reduces risk but does not guarantee correctness.
- Cached reports require invalidation when policy or evaluator logic changes.
- Human review is necessary before making legal or business decisions.

## Security Notes

- Never commit passwords, API keys, `.env`, or real contracts.
- Add authentication and authorization before exposing the API beyond localhost.
- Enforce upload limits and validate files server-side.
- Avoid returning raw exception details to clients in production.
- Define retention and deletion rules for uploaded PDFs, extracted text, chunks, and cached reports.

## Future Improvements

- Policy and prompt versioning for cache invalidation.
- OCR support for scanned PDFs.
- Authentication and organization-specific policies.
- Audit logs and report version history.
- Stronger evidence-grounding tests.
- Background jobs for long-running analysis.
- Deployment configuration and monitoring.

## Disclaimer

This project is for learning and demonstration. It does not replace legal advice or a formal compliance audit. Do not upload confidential contracts unless you have permission and have reviewed the application's data handling and security controls.
