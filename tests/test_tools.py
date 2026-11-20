import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from planner import plan_trip
from tools import estimate_budget, search_flights, search_hotels, search_places


def test_direct_flight_cheapest():
    r = search_flights("Delhi", "Kolkata")
    assert r["direct"] and r["cheapest"]["price"] == 3779


def test_one_stop_fallback():
    r = search_flights("Delhi", "Goa")
    assert not r["direct"] or r["cheapest"] is None or r["cheapest"]["price"] > 0


def test_hotels_filter():
    hs = search_hotels("Goa", min_stars=5, max_price=3000)
    assert hs and all(h["stars"] >= 5 and h["price_per_night"] <= 3000 for h in hs)


def test_places_sorted():
    ps = search_places("Kolkata", min_rating=4.5)
    assert ps == sorted(ps, key=lambda p: -p["rating"])


def test_budget():
    assert estimate_budget(4800, 3200, 2, 2500 / 3, 1)["hotel"] == 6400


def test_plan_structure():
    plan = plan_trip("Delhi", "Kolkata", "2026-12-12", 3)
    assert len(plan["itinerary"]) == 3 and plan["budget"]["total"] > 0
