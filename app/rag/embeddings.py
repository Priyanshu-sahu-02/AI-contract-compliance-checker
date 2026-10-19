from langchain_huggingface import HuggingFaceEmbeddings

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _model

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.embed_documents(texts)

def generate_query_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    return model.embed_query(text)