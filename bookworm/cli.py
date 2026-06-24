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

    subcommand = sys.argv[1] if len(sys.argv) > 1 else "gui" # Opens GUI by default

    try:
        config = load_config(working_dir=Path.cwd())
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    if subcommand == "gui":
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        from .gui import AppController, GUIConfig

        app = QApplication(sys.argv)
        gui_config = GUIConfig.from_config(config)
        controller = AppController(config, gui_config)
        controller.window.show()
        QTimer.singleShot(0, controller.main_panel_controller.refresh_message_layouts)
        return app.exec()
    
    if subcommand == "terminal":
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
        
    if subcommand == "index":
        from .rag.indexer import build_index
        print(build_index(config))
        return 0

    print(f"Unknown command '{subcommand}'. Usage: bookworm [gui|terminal|index]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())