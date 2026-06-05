import os
from pathlib import Path

from dotenv import load_dotenv

from.agent import main as agent_main

def main() -> None: 
    repo_root = Path(__file__).resolve.parent.parent
    
    load_dotenv(repo_root / ".env")

    os.environ.setdefault("WORKING_DIR", os.getcwd())

    agent_main()