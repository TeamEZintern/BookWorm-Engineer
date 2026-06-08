
import os 
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Config: 
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    context_window: int
    git_user_name: str
    git_user_email: str
    working_dir: Path

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
    
def load_config(working_dir: Path | None = None) -> Config:
    resolved_working_dir = working_dir or Path.cwd()

    return Config(
        llm_api_key=_required_env("LLM_API_KEY"),
        llm_base_url=_optional_env("LLM_BASE_URL","https://openrouter.ai/api/v1"),
        llm_model=_optional_env("LLM_MODEL","openai/gpt-4o-mini"),
        context_window=_int_env("CONTEXT_WINDOW",128000),
        git_user_name=_optional_env("GIT_USER_NAME", "BookWorm Engineer"),
        git_user_email=_optional_env("GIT_USER_EMAIL", "bookworm@example.com"),
        working_dir=resolved_working_dir.resolve(),
    )