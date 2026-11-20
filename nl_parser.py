"""Rule-based natural-language parser: lets the agent tab work without an LLM."""
import re
from datetime import date, timedelta

from config import CITY_COORDS
from tools import list_place_types

ALL_TYPES = sorted({t for c in CITY_COORDS for t in list_place_types(c)})


def parse_request(text: str) -> dict:
    """Extract trip parameters from free text. Raises ValueError if cities missing."""
    low = text.lower()
    cities = {c.lower(): c for c in CITY_COORDS}
    src = re.search(r"from\s+([a-z]+)", low)
    dst = re.search(r"\bto\s+([a-z]+)", low)
    source = cities.get(src.group(1)) if src else None
    dest = cities.get(dst.group(1)) if dst else None
    if not (source and dest):  # fall back to order of appearance
        order = [cities[k] for k in sorted((k for k in cities if k in low), key=low.find)]
        source, dest = source or (order[0] if order else None), dest or (order[1] if len(order) > 1 else None)
    if not source or not dest or source == dest:
        raise ValueError("Please mention both cities, e.g. 'from Delhi to Kolkata'. "
                         f"Available: {', '.join(sorted(CITY_COORDS))}.")
    d = re.search(r"\d{4}-\d{2}-\d{2}", text)
    days = re.search(r"(\d+)[\s-]*day", low)
    budget = re.search(r"budget[^\d]{0,15}([\d,\.]+)\s*(k)?", low)
    amount = None
    if budget:
        amount = float(budget.group(1).replace(",", "").rstrip(".") or 0)
        amount *= 1000 if budget.group(2) else 1
    people = re.search(r"(\d+)\s*(?:people|persons|travell?ers|adults)", low)
    return {
        "source": source, "destination": dest,
        "start_date": d.group(0) if d else (date.today() + timedelta(days=30)).isoformat(),
        "num_days": int(days.group(1)) if days else 3,
        "budget": amount, "travelers": int(people.group(1)) if people else 1,
        "preferred_types": [t for t in ALL_TYPES if t in low],
        "round_trip": "return" in low or "round" in low,
    }
