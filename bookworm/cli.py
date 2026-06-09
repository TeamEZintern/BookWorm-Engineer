import sys
from pathlib import Path

from dotenv import load_dotenv

from .agent import Agent
from .config import ConfigError, load_config
from .llm import create_client
from .prompts import build_system_prompt
from .tools import create_tool_registry


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    subcommand = sys.argv[1] if len(sys.argv) > 1 else "chat"

    try:
        config = load_config(working_dir=Path.cwd())
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    if subcommand == "index":
        from .rag.indexer import build_index
        print(build_index(config))
        return 0

    if subcommand == "chat":
        client = create_client(config)
        tool_registry = create_tool_registry(config)
        system_prompt = build_system_prompt(config)

        agent = Agent(
            config=config,
            client=client,
            tool_registry=tool_registry,
            system_prompt=system_prompt,
        )
        agent.run()
        return 0

    print(f"Unknown command '{subcommand}'. Usage: bookworm [chat|index]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())