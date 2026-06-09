from pathlib import Path

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bookworm.config import Config
from bookworm.rag.embeddings import create_embeddings

SUPPORTED_EXTENSIONS = {".txt", ".md"}

def _get_sources_dir(config: Config) -> Path: 
    return getattr(config, "rag_sources_dir", Path(".bookworm/sources"))

def _get_index_dir(config: Config) -> Path: 
    return getattr(config, "rag_index_dir", Path(".bookworm/index"))

def _get_chunk_size(config: Config) -> int:
    return getattr(config, "rag_chunk_size", 800)

def _get_chunk_overlap(config: Config) -> int:
    return getattr(config, "rag_chunk_overlap", 120)

def _get_collection_name(config: Config) -> str:
    return getattr(config,"rag_collection_name", "bookworm_sources")

def _load_text_documents(sources_dir: Path) -> list[Document]:
    """
    Load .txt and .md files from .bookworm/sources.

    Each loaded file becomes one LangChain Document before chunking.
    """

    documents: list[Document] = []

    for file_path in sources_dir.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try: 
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8", errors="ignore")

        if not text.strip():
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(file_path),
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "file_type": file_path.suffix.lower(),
                },
            )
        )
    
    return documents

def build_index(config: Config) -> str:
    """
    Build or refresh the ChromaDB index from .bookworm/sources.

    It should not touch agent.py
    """

    sources_dir = _get_sources_dir(config)
    index_dir = _get_index_dir(config)

    sources_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    documents = _load_text_documents(sources_dir)

    if not documents: 
        return (
            f"No supported doucments found in {sources_dir}. "
            "Add .txt or .md files, then run `bookworm index` again. "
        )
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_get_chunk_size(config),
        chunk_overlap=_get_chunk_overlap(config),
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        return f"No indexable chunks were created from documents in {sources_dir}."
    
    embeddings = create_embeddings(config)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(index_dir),
        collection_name=_get_collection_name(config),
    )

    return (
        f"Indexed {len(documents)} documents into {len(chunks)} chunks"
        f"at {index_dir}"
    )