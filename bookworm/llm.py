from openai import OpenAI

from .config import Config

def create_client(config: Config) -> OpenAI:
    kwargs: dict = {
        "api_key": config.llm_api_key,
        "base_url": config.llm_base_url,
    }
    if "openrouter.ai" in config.llm_base_url:
        kwargs["default_headers"] = {"X-OpenRouter-Title": "BookWorm Engineer"}
    return OpenAI(**kwargs)