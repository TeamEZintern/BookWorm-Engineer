from pathlib import Path
from types import SimpleNamespace

from bookworm.rag import indexer


class FakeChroma:
    calls: list[dict] = []

    @classmethod
    def from_documents(cls, **kwargs):
        cls.calls.append(kwargs)
        return object()

class FakePdfPage:
    def __init__(self, text: str | None):
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


class FakePdfReader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pages = [
            FakePdfPage("Page one content"),
            FakePdfPage("   "),
            FakePdfPage(None),
            FakePdfPage("Page four content"),
        ]

def test_load_text_documents_reads_supported_non_empty_files(tmp_path):
    sources_dir = tmp_path / "sources"
    nested_dir = sources_dir / "nested"
    nested_dir.mkdir(parents=True)

    markdown_file = sources_dir / "notes.md"
    text_file = nested_dir / "guide.TXT"
    ignored_file = sources_dir / "image.png"
    empty_file = sources_dir / "empty.md"

    markdown_file.write_text("# Notes\nUseful content", encoding="utf-8")
    text_file.write_text("Plain text content", encoding="utf-8")
    ignored_file.write_text("not indexable", encoding="utf-8")
    empty_file.write_text("   \n", encoding="utf-8")

    documents = indexer._load_text_documents(sources_dir)

    assert [document.metadata["file_name"] for document in documents] == [
        "notes.md",
        "guide.TXT",
    ]
    assert [document.metadata["file_type"] for document in documents] == [".md", ".txt"]
    assert [document.page_content for document in documents] == [
        "# Notes\nUseful content",
        "Plain text content",
    ]
    assert all(Path(document.metadata["file_path"]).exists() for document in documents)


def test_load_text_documents_ignores_bad_utf8_bytes(tmp_path):
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    source_file = sources_dir / "legacy.txt"
    source_file.write_bytes(b"valid prefix \xff\xfe valid suffix")

    documents = indexer._load_text_documents(sources_dir)

    assert len(documents) == 1
    assert documents[0].metadata["file_name"] == "legacy.txt"
    assert "valid prefix" in documents[0].page_content
    assert "valid suffix" in documents[0].page_content


def test_build_index_creates_dirs_and_returns_message_when_no_documents(tmp_path):
    config = SimpleNamespace(
        rag_sources_dir=tmp_path / "sources",
        rag_index_dir=tmp_path / "index",
    )

    result = indexer.build_index(config)

    assert "No supported" in result
    assert "Add .txt, .md, or text-based .pdf files" in result
    assert str(config.rag_sources_dir) in result
    assert config.rag_sources_dir.exists()
    assert config.rag_index_dir.exists()


def test_build_index_splits_documents_and_writes_chroma_collection(
    monkeypatch, tmp_path
):
    FakeChroma.calls.clear()
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    (sources_dir / "guide.md").write_text("Alpha\n\nBeta", encoding="utf-8")
    fake_embeddings = object()
    config = SimpleNamespace(
        rag_sources_dir=sources_dir,
        rag_index_dir=tmp_path / "index",
        rag_chunk_size=100,
        rag_chunk_overlap=10,
        rag_collection_name="test_collection",
    )
    monkeypatch.setattr(indexer, "Chroma", FakeChroma)
    monkeypatch.setattr(indexer, "create_embeddings", lambda received: fake_embeddings)

    result = indexer.build_index(config)

    assert "Indexed 1 documents into" in result
    assert str(config.rag_index_dir) in result

    assert len(FakeChroma.calls) == 1
    chroma_call = FakeChroma.calls[0]
    assert chroma_call["embedding"] is fake_embeddings
    assert chroma_call["persist_directory"] == str(config.rag_index_dir)
    assert chroma_call["collection_name"] == "test_collection"
    assert len(chroma_call["documents"]) >= 1
    assert chroma_call["documents"][0].page_content == "Alpha\n\nBeta"
    assert chroma_call["documents"][0].metadata["file_name"] == "guide.md"

def test_build_index_splits_long_documents_into_multiple_chunks(monkeypatch, tmp_path):
    FakeChroma.calls.clear()

    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    long_text = "A" * 120 + "\n\n" + "B" * 120
    (sources_dir / "long.md").write_text(long_text, encoding="utf-8")

    fake_embeddings = object()
    config = SimpleNamespace(
        rag_sources_dir=sources_dir,
        rag_index_dir=tmp_path / "index",
        rag_chunk_size=100,
        rag_chunk_overlap=10,
        rag_collection_name="test_collection",
    )

    monkeypatch.setattr(indexer, "Chroma", FakeChroma)
    monkeypatch.setattr(indexer, "create_embeddings", lambda received: fake_embeddings)

    result = indexer.build_index(config)

    chroma_call = FakeChroma.calls[0]

    assert len(chroma_call["documents"]) > 1
    assert all(chunk.metadata["file_name"] == "long.md" for chunk in chroma_call["documents"])

def test_load_text_documents_reads_pdf_pages(monkeypatch, tmp_path):
    monkeypatch.setattr(indexer, "PdfReader", FakePdfReader)

    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    pdf_file = sources_dir / "manual.pdf"
    pdf_file.write_bytes(b"%PDF fake test bytes")

    documents = indexer._load_text_documents(sources_dir)

    assert len(documents) == 2
    assert [document.page_content for document in documents] == [
        "Page one content",
        "Page four content",
    ]
    assert [document.metadata["page"] for document in documents] == [1, 4]
    assert all(document.metadata["file_name"] == "manual.pdf" for document in documents)
    assert all(document.metadata["file_type"] == ".pdf" for document in documents)