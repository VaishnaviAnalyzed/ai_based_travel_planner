"""Places Discovery Tool: recommends attractions from places.json."""
from data_loader import load_json, same


def list_place_types(city: str) -> list:
    """All place categories available in a city."""
    return sorted({p["type"] for p in load_json("places.json") if same(p["city"], city)})


def search_places(city: str, types: list = None, min_rating: float = 0.0,
                  limit: int = 10) -> list:
    """Attractions in `city`, filtered by type / rating, best rated first."""
    wanted = {t.lower() for t in (types or [])}
    places = [
        p for p in load_json("places.json")
        if same(p["city"], city)
        and p["rating"] >= min_rating
        and (not wanted or p["type"].lower() in wanted)
    ]
    places.sort(key=lambda p: -p["rating"])
    return places[:limit]
