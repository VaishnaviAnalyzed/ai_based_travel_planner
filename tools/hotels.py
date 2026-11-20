"""Hotel Recommendation Tool: filters hotels.json by city, stars, price."""
from data_loader import load_json, same


def search_hotels(city: str, min_stars: int = 0, max_price: float = None,
                  amenities: list = None, sort_by: str = "best_value",
                  limit: int = 5) -> list:
    """Return hotels in `city`.

    sort_by: 'best_value' (stars per rupee), 'stars' (highest rated first),
    or 'price' (cheapest first).
    """
    wanted = {a.lower() for a in (amenities or [])}
    hotels = [
        h for h in load_json("hotels.json")
        if same(h["city"], city)
        and h["stars"] >= min_stars
        and (max_price is None or h["price_per_night"] <= max_price)
        and wanted <= set(h["amenities"])
    ]
    sorters = {
        "best_value": lambda h: -(h["stars"] / h["price_per_night"]),
        "stars": lambda h: (-h["stars"], h["price_per_night"]),
        "price": lambda h: h["price_per_night"],
    }
    hotels.sort(key=sorters.get(sort_by, sorters["best_value"]))
    return hotels[:limit]
