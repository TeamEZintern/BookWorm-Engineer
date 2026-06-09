
import os 
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Config: 
    # LLM config
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    context_window: int

    # Git config
    git_user_name: str
    git_user_email: str

    # Project config
    working_dir: Path

    # RAG config
    rag_sources_dir: Path
    rag_index_dir: Path
    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_top_k: int
    rag_collection_name: str
    rag_embedding_model: str

class ConfigError(RuntimeError):
    pass

def _required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ConfigError(f"Missing required environment variable: {name}")
    
    return value.strip()

def _optional_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default

def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        return default
    
    try: 
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got: {raw_value!r}") from exc
    
def _path_env(name: str, default: str, working_dir: Path) -> Path:
    raw_value = _optional_env(name, default)
    path = Path(raw_value)

    if path.is_absolute():
        return path.resolve()
    
    return (working_dir / path).resolve()

def load_config(working_dir: Path | None = None) -> Config:
    resolved_working_dir = working_dir or Path.cwd()

    return Config(
        # LLM config
        llm_api_key=_required_env("LLM_API_KEY"),
        llm_base_url=_optional_env("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        llm_model=_optional_env("LLM_MODEL","openai/gpt-4o-mini"),
        context_window=_int_env("CONTEXT_WINDOW",128000,),

        # Git config
        git_user_name=_optional_env("GIT_USER_NAME","BookWorm Engineer"),
        git_user_email=_optional_env("GIT_USER_EMAIL","bookworm@example.com"),

        # Project config
        working_dir=resolved_working_dir,

        # RAG config
        rag_sources_dir=_path_env("RAG_SOURCES_DIR",".bookworm/sources",resolved_working_dir),
        rag_index_dir=_path_env("RAG_INDEX_DIR",".bookworm/index",resolved_working_dir),
        rag_chunk_size=_int_env("RAG_CHUNK_SIZE",800),
        rag_chunk_overlap=_int_env("RAG_CHUNK_OVERLAP",120),
        rag_top_k=_int_env("RAG_TOP_K",5),
        rag_collection_name=_optional_env("RAG_COLLECTION_NAME","bookworm_sources"),
        rag_embedding_model=_optional_env("RAG_EMBEDDING_MODEL","sentence-transformers/all-MiniLM-L6-v2"),
    )