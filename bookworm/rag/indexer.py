from pathlib import Path
from pypdf import PdfReader

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bookworm.config import Config
from bookworm.rag.embeddings import create_embeddings

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

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

def _document_metadata(file_path: Path, **extra_metadata: object) -> dict:
    return {
        "source": str(file_path),
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_type": file_path.suffix.lower(),
        **extra_metadata,
    }

def _load_plain_text_document(file_path: Path) -> Document:
    try: 
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    
    if not text.strip():
        return None
    
    return Document(
        page_content=text,
        metadata=_document_metadata(file_path),
    )

def _load_pdf_documents(file_path: Path) -> list[Document]:
    documents: list[Document] = []
    
    reader = PdfReader(str(file_path))

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if not text.strip():
            continue
        
        documents.append(
            Document(
                page_content=text,
                metadata=_document_metadata(
                    file_path,
                    page=page_index,
                ),
            )
        )

    return documents

def _load_text_documents(sources_dir: Path) -> list[Document]:
    """
    Load supported source files from .bookworm/sources.

    .txt and .md files become one Document each.
    .pdf files become one Document per text-bearing page.
    """

    documents: list[Document] = []

    for file_path in sources_dir.rglob("*"):
        if not file_path.is_file():
            continue

        file_type = file_path.suffix.lower()

        if file_type not in SUPPORTED_EXTENSIONS:
            continue

        if file_type in {".txt",".md"}:
            document = _load_plain_text_document(file_path)

            if document is not None: 
                documents.append(document)
            
            continue

        if file_type == ".pdf":
            documents.extend(_load_pdf_documents(file_path))
    
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
            f"No supported documents found in {sources_dir}. "
            "Add .txt, .md, or text-based .pdf files, then run `bookworm index` again. "
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
        f" at {index_dir}"
    )