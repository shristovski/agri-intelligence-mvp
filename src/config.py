import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"


def load_sources() -> dict:
    path = CONFIG_DIR / "sources.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_env():
    load_dotenv(ROOT_DIR / ".env")


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)
