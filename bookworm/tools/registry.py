import json
from dataclasses import dataclass
from typing import Callable

from ..config import Config
from .implementation import create_implementations
from .schema import SCHEMA


@dataclass(frozen=True)
class ToolRegistry:
    schema: list[dict]
    implementations: dict[str, Callable[..., str]]


def create_tool_registry(
    config: Config,
    ask_user_fn: Callable[[str], str] | None = None,
) -> ToolRegistry:
    return ToolRegistry(
        schema=SCHEMA,
        implementations=create_implementations(config, ask_user_fn=ask_user_fn),
    )

def call_tool(registry: ToolRegistry, name: str, arguments_json: str) -> str:
    if name not in registry.implementations:
        return f"Unknown tool: {name}"
    
    try: 
        arguments = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc: 
        return f"Invalid tool arguments JSON: {exc}"
    
    try: 
        return str(registry.implementations[name](**arguments))
    except TypeError as exc: 
        return f"Error calling {name}: {exc}. Tool arguments must be named correctly"
    except Exception as exc:
        return f"Tool {name!r} failed: {exc}" 