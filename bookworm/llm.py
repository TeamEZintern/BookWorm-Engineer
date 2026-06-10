from langchain_openrouter import ChatOpenRouter

from .config import Config

def create_client(config: Config) -> ChatOpenRouter:
    return ChatOpenRouter(
        model=config.llm_model,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        temperature=0,
        reasoning={"effort": "low"},
        app_title="BookWorm Engineer",
    )