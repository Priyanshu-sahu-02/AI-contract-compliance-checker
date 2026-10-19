from pathlib import Path

from app.ingestion.parser import extract_text, split_text
from app.rag.embeddings import generate_embeddings
from app.database import initialize_database, save_chunks

def ingest_pdf(file_path: str):
    pdf_path = Path(file_path)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print(f"Extracting pdf text . . .")
    text = extract_text(str(pdf_path))

    if not text.strip():
        raise ValueError("No extractable text found in PDF.")

    print("2. splitting text into chunks . . .")
    chunks = split_text(text)

    if not chunks:
        raise ValueError("No text chunks generated.")

    print(f"total chunks : {len(chunks)}")

    print("3. generating embeddings for chunks ....")
    vectors = generate_embeddings(chunks)

    print("4. Saving chunks to PostgreSQL...")
    initialize_database()
    save_chunks(chunks, vectors, pdf_path.name)

    print("PDF ingestion completed successfully!")

if __name__ == "__main__":
    ingest_pdf("sample_contract_compliance_test.pdf")