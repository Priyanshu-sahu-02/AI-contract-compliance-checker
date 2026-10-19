from pgvector.psycopg import register_vector


from app.database import get_connection
from app.rag.embeddings import generate_query_embedding


def search_similar_chunks(query: str, document_name: str | None = None, k: int = 5):
    if not query.strip():
        raise ValueError("Search query cannot be empty.")
    if k < 1:
        raise ValueError("k must be at least 1.")

    query_vector = generate_query_embedding(query)

    # Convert the embedding to pgvector's text representation
    vector_text = "[" + ",".join(map(str, query_vector)) + "]"

    with get_connection() as conn:
        if document_name:
            rows = conn.execute(
                """
                SELECT document_name, chunk_text,
                       embedding <=> %s::vector AS distance
                FROM contract_chunks
                WHERE document_name = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector_text, document_name, vector_text, k),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT document_name, chunk_text,
                       embedding <=> %s::vector AS distance
                FROM contract_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (vector_text, vector_text, k),
            ).fetchall()

    return [
        {
            "document_name": row[0],
            "chunk_text": row[1],
            "distance": float(row[2]),
        }
        for row in rows
    ]
            
     