import hashlib
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.database import (
    initialize_database,
    get_document_by_hash,
    register_document,
    mark_document_complete,
    delete_document_registration,
    get_cached_report,
    save_cached_report,
    mark_document_ready,
    delete_document_chunks
)
from app.ingestion.ingest import ingest_pdf
from app.graph.workflow import run_compliance_check

app = FastAPI(title="AI Contract Compliance Checker")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def calculate_sha256(file_path: Path) -> str:
    """Calculate a PDF's SHA-256 hash without reading it all into memory."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


@app.on_event("startup")
def startup():
    initialize_database()


@app.get("/")
def home():
    return {"message": "AI Contract Compliance Checker API is running"}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_pdf(file_path: Path) -> None:
    """Validate PDF readability and enforce the upload size limit."""

    if not file_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Uploaded file could not be found.",
        )

    file_size = file_path.stat().st_size

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF is too large. Maximum allowed size is 10 MB.",
        )

    try:
        reader = PdfReader(str(file_path), strict=True)

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Password-protected PDFs are not supported.",
            )

        if len(reader.pages) == 0:
            raise HTTPException(
                status_code=400,
                detail="The PDF contains no pages.",
            )

        # Read page content to catch some malformed PDFs early.
        for page in reader.pages:
            page.extract_text()

    except HTTPException:
        raise
    except (PdfReadError, ValueError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted PDF. Please upload a valid PDF.",
        ) from exc



@app.post("/check-contract")
def check_contract(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    file_path = UPLOAD_DIR / f"{uuid4().hex}.pdf"
    document_hash = None
    registered_by_this_request = False
    ingestion_succeeded = False

    try:
        # 1. Save PDF with a 10 MB size limit.
        total_size = 0

        with file_path.open("wb") as destination:
            while chunk := file.file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF is too large. Maximum allowed size is 10 MB.",
                    )

                destination.write(chunk)

        # 2. Validate PDF before database operations.
        validate_pdf(file_path)

        # 3. Calculate content hash.
        document_hash = calculate_sha256(file_path)

        # 4. Check whether this PDF already exists.
        existing = get_document_by_hash(document_hash)

        if existing:
            status = existing["status"]
            stored_name = existing["document_name"]

            # Return cached report if available.
            if status == "completed":
                cached_report = get_cached_report(document_hash)

                if cached_report is not None:
                    cached_report["document_reused"] = True
                    cached_report["cache_hit"] = True
                    return cached_report

                # Completed record, but cache is missing.
                report = run_compliance_check(stored_name)
                save_cached_report(document_hash, report)
                mark_document_complete(document_hash)

                report["document_reused"] = True
                report["cache_hit"] = False
                return report

            # Chunks already exist; retry report generation only.
            if status == "ready":
                report = run_compliance_check(stored_name)
                save_cached_report(document_hash, report)
                mark_document_complete(document_hash)

                report["document_reused"] = True
                report["cache_hit"] = False
                return report

            # Another request may still be processing this PDF.
            raise HTTPException(
                status_code=409,
                detail="This PDF is already being processed. Please try again shortly.",
            )

        # 5. Register a new PDF.
        registered_by_this_request = register_document(
            document_hash,
            file_path.name,
        )

        if not registered_by_this_request:
            # Another request may have registered the hash meanwhile.
            existing = get_document_by_hash(document_hash)

            if existing and existing["status"] == "completed":
                cached_report = get_cached_report(document_hash)

                if cached_report is not None:
                    cached_report["document_reused"] = True
                    cached_report["cache_hit"] = True
                    return cached_report

            raise HTTPException(
                status_code=409,
                detail="This PDF is already being processed. Please try again shortly.",
            )

        # 6. Ingest the new PDF.
        try:
            ingest_pdf(str(file_path))
            mark_document_ready(document_hash)
            ingestion_succeeded = True

        except Exception as exc:
            # Remove partial chunks and registration only
            # when ingestion fails.
            try:
                delete_document_chunks(file_path.name)
                delete_document_registration(document_hash)
                registered_by_this_request = False
            except Exception as cleanup_error:
                print(f"Cleanup failed: {cleanup_error}")

            raise HTTPException(
                status_code=500,
                detail="PDF ingestion failed. Please retry.",
            ) from exc

        # 7. Generate and cache the report.
        # If this fails, preserve the ready document and chunks
        # so a retry can skip ingestion.
        try:
            report = run_compliance_check(file_path.name)
            save_cached_report(document_hash, report)
            mark_document_complete(document_hash)

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Report generation failed. The PDF was ingested; "
                    "please retry to generate the report."
                ),
            ) from exc

        report["document_reused"] = False
        report["cache_hit"] = False
        return report

    except HTTPException:
        # Do not delete successfully ingested chunks when
        # report generation fails.
        if registered_by_this_request and not ingestion_succeeded:
            try:
                delete_document_chunks(file_path.name)
                delete_document_registration(document_hash)
            except Exception as cleanup_error:
                print(f"Cleanup failed: {cleanup_error}")
        raise

    except Exception as exc:
        if registered_by_this_request and not ingestion_succeeded:
            try:
                delete_document_chunks(file_path.name)
                delete_document_registration(document_hash)
            except Exception as cleanup_error:
                print(f"Cleanup failed: {cleanup_error}")

        raise HTTPException(
            status_code=500,
            detail="Contract processing failed. Please retry.",
        ) from exc

    finally:
        file.file.close()

        if file_path.exists():
            file_path.unlink()

    