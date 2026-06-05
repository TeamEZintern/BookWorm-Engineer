from dataclasses import dataclass
from typing import Callable

from ..config import Config
from .implementation import create_implementations
from .schema import schema


@dataclass(frozen=True)
class ToolRegistry:
    schema: list[dict]
    implementations: dict[str, Callable[..., str]]


def create_tool_registry(config: Config) -> ToolRegistry:
    return ToolRegistry(
        schema=schema,
        implementations=create_implementations(config),
    )