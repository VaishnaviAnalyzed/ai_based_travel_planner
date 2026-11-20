"""Flight Search Tool: filters flights.json by route, finds cheapest / fastest."""
from datetime import datetime

from data_loader import load_json, same


def _enrich(flight: dict) -> dict:
    delta = (datetime.fromisoformat(flight["arrival_time"])
             - datetime.fromisoformat(flight["departure_time"]))
    return {**flight, "duration_minutes": int(delta.total_seconds() // 60)}


def _one_stop(source: str, destination: str) -> list:
    """Build one-stop connections when no direct flight exists."""
    flights = load_json("flights.json")
    firsts = [f for f in flights if same(f["from"], source)]
    seconds = [f for f in flights if same(f["to"], destination)]
    combos = []
    for a in firsts:
        for b in seconds:
            if a["to"] == b["from"]:
                legs = [_enrich(a), _enrich(b)]
                combos.append({
                    "via": a["to"], "legs": legs,
                    "airline": f'{a["airline"]} + {b["airline"]}',
                    "price": a["price"] + b["price"],
                    "duration_minutes": sum(x["duration_minutes"] for x in legs),
                })
    return combos


def search_flights(source: str, destination: str, date: str = None,
                   sort_by: str = "price") -> dict:
    """Search flights source -> destination.

    date: optional 'YYYY-MM-DD'. The sample dataset only has 2025 dates, so if
    nothing matches the date we return all flights on the route and flag it.
    sort_by: 'price' or 'duration'.
    """
    flights = [_enrich(f) for f in load_json("flights.json")
               if same(f["from"], source) and same(f["to"], destination)]
    date_matched, direct = False, True
    if date:
        on_date = [f for f in flights if f["departure_time"].startswith(date)]
        if on_date:
            flights, date_matched = on_date, True
    if not flights:
        flights, direct = _one_stop(source, destination), False
    key = "duration_minutes" if sort_by == "duration" else "price"
    flights.sort(key=lambda f: f[key])
    return {
        "source": source, "destination": destination, "direct": direct,
        "date_matched": date_matched, "options": flights[:5],
        "cheapest": min(flights, key=lambda f: f["price"]) if flights else None,
        "fastest": min(flights, key=lambda f: f["duration_minutes"]) if flights else None,
    }
