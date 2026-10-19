import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector 
from psycopg.types.json import Jsonb

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not in .env")
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_hash TEXT PRIMARY KEY,
                document_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'processing',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        conn.execute("""
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS report JSONB
        """)
    print("Database connected. contract_chunks table is ready.")

def get_cached_report(document_hash: str):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT report
                FROM documents
                WHERE document_hash = %s
                  AND status = 'completed'
                  AND report IS NOT NULL
                """,
                (document_hash,),
            )
            row = cur.fetchone()

        conn.commit()
        return row[0] if row else None

    finally:
        conn.close()


def save_cached_report(document_hash: str, report: dict):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET report = %s
                WHERE document_hash = %s
                """,
                (Jsonb(report), document_hash),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def save_chunks(chunks, vectors, document_name):
    if len(chunks) != len(vectors):
        raise ValueError("Chunks and vectors count must be the same")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO contract_chunks(document_name, chunk_text, embedding)
                values(%s, %s, %s)
                """,
                [(document_name, chunk, vector) 
                for chunk, vector in zip(chunks, vectors) 
                ],
            )
    print(f"Saved {len(chunks)} chunks to PostgreSQL.")

def delete_document_chunks(document_name: str):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM contract_chunks
                WHERE document_name = %s
                """,
                (document_name,),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_document_by_hash(document_hash: str):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT document_name, status
                FROM documents
                WHERE document_hash = %s
                """,
                (document_hash,),
            )
            row = cur.fetchone()

        conn.commit()

        if row is None:
            return None

        return {
            "document_name": row[0],
            "status": row[1],
        }

    finally:
        conn.close()


def register_document(document_hash: str, document_name: str) -> bool:
    """Reserve a hash. True means this caller registered it first."""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (
                    document_hash, document_name, status
                )
                VALUES (%s, %s, 'processing')
                ON CONFLICT (document_hash) DO NOTHING
                RETURNING document_hash
                """,
                (document_hash, document_name),
            )
            inserted = cur.fetchone() is not None

        conn.commit()
        return inserted

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def mark_document_ready(document_hash: str):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET status = 'ready'
                WHERE document_hash = %s
                """,
                (document_hash,),
            )
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def mark_document_complete(document_hash: str):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET status = 'completed'
                WHERE document_hash = %s
                """,
                (document_hash,),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def delete_document_registration(document_hash: str):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM documents
                WHERE document_hash = %s
                  AND status = 'processing'
                """,
                (document_hash,),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()