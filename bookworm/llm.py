from openai import OpenAI

from .config import Config

def create_client(config: Config) -> OpenAI:
    return OpenAI(
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        default_headers={
            "X-OpenRouter-Title": "BookWorm Engineer"
        },
    )