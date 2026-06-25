import json
import time

from openai import (
    OpenAI,
    InternalServerError,
    APIConnectionError,
    RateLimitError,
)

from .config import Config

MAX_API_RETRIES = 4
RETRY_BASE_DELAY = 2.0

def create_client(config: Config) -> OpenAI:
    kwargs: dict = {
        "api_key": config.llm_api_key,
        "base_url": config.llm_base_url,
    }
    if "openrouter.ai" in config.llm_base_url:
        kwargs["default_headers"] = {"X-OpenRouter-Title": "BookWorm Engineer"}
    return OpenAI(**kwargs)

def complete_with_retry(client: OpenAI, *, on_retry=None, **kwargs):
    """
    Call chat.completions.create, retrying transient failures with backoff.

    Retries connection / rate-limit / 5xx errors and the raw json.JSONDecordError that a gateway
    throws when it returns a non-JSON body on overlaod.

    Real 4xx client erros are left to raise immediatrly. `on_retry(exc, attempt, delay)` is an optional hook so callers
    can print progree
    """

    last_exc: Exception | None = None
    for attempt in range (1, MAX_API_RETRIES + 1):
        try: 
            return client.chat.completions.create(**kwargs)
        except(
            APIConnectionError,
            RateLimitError,
            InternalServerError,
            json.JSONDecodeError,
        ) as exc:
            last_exc = exc
            if attempt == MAX_API_RETRIES:
                break 
            delay = RETRY_BASE_DELAY * 2 ** (attempt - 1)
            if on_retry:
                on_retry(exc, attempt, delay)
            time.sleep(delay)
        
    raise RuntimeError(
        f"LLM request failed after {MAX_API_RETRIES} attempts: {last_exc}"
    ) from last_exc
