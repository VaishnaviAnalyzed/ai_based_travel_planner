"""JSON dataset loading with caching and error handling."""
import json
from functools import lru_cache

from config import DATA_DIR


@lru_cache(maxsize=None)
def load_json(filename: str) -> list:
    """Load a dataset from the data/ folder. Returns [] if unreadable."""
    try:
        with open(DATA_DIR / filename, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[data_loader] Could not load {filename}: {exc}")
        return []


def same(a: str, b: str) -> bool:
    """Case-insensitive string comparison."""
    return str(a).strip().lower() == str(b).strip().lower()
