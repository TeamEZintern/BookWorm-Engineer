from pathlib import Path


def save(artifacts_dir: Path, name: str, content: str) -> None:
    path = artifacts_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load(artifacts_dir: Path, name: str) -> str | None:
    path = artifacts_dir / name
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
