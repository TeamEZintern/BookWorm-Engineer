from langchain_huggingface import HuggingFaceEmbeddings

from bookworm.config import Config

def create_embeddings(config: Config) -> HuggingFaceEmbeddings:
    """
    Create the embedding model used for RAG indexing and retrieval.

    MVP choice: 
    - Local model 
    - No OpenAI/OpenRouter embedding dependency
    - Good enough for .txt/.md project notes
    """

    model_name = getattr(
        config,
        "rag_embedding_model",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    return HuggingFaceEmbeddings(
        model_name=model_name,
    )