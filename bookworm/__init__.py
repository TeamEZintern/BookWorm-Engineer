import os
import sys

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_PKG_DIR)

if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_REPO_ROOT, ".env"))

os.environ["WORKING_DIR"] = os.getcwd()

import agent


def main() -> None:
    agent.main()
