"""Rule-based planner: chains the tools and explains every decision.

Produces the same structured output the LLM agent targets (JSON + markdown),
so the app works even without an LLM key.
"""
import math
from datetime import date, timedelta

from config import DEFAULT_DAILY_EXPENSE
from tools import (estimate_budget, get_weather, search_flights,
                   search_hotels, search_places)


def _legs(option):
    return option.get("legs", [option]) if option else []


def _flight_summary(option):
    legs = _legs(option)
    return {
        "airline": option["airline"], "price_per_person": option["price"],
        "stops": len(legs) - 1,
        "legs": [{"flight_id": l["flight_id"], "from": l["from"], "to": l["to"],
                  "departs": l["departure_time"], "arrives": l["arrival_time"]}
                 for l in legs],
    }


def plan_trip(source, destination, start_date, num_days, travelers=1, budget=None,
              min_stars=3, preferred_types=None, daily_expense=DEFAULT_DAILY_EXPENSE,
              round_trip=False, prefer_flight="price"):
    """Build a complete day-wise trip plan as a dict."""
    if num_days < 1:
        raise ValueError("num_days must be at least 1")
    start = start_date if isinstance(start_date, date) else date.fromisoformat(start_date)
    end = start + timedelta(days=num_days - 1)
    nights, rooms = num_days - 1, math.ceil(travelers / 2)
    why = []

    # --- Flights
    out = search_flights(source, destination, start.isoformat(), prefer_flight)
    flight = out["cheapest"] if prefer_flight == "price" else out["fastest"]
    if not flight:
        raise ValueError(f"No flights (direct or one-stop) from {source} to {destination}.")
    flight_cost = flight["price"] * travelers
    kind = "direct" if out["direct"] else f'1-stop via {flight["via"]}'
    why.append(f"Flight: picked the {'cheapest' if prefer_flight == 'price' else 'fastest'} "
               f"{kind} option ({flight['airline']}, ₹{flight['price']:,}).")
    if not out["date_matched"]:
        why.append("Dataset has no flight on your exact date, so the closest-fit route "
                   "option is shown (sample flights are dated 2025).")
    return_flight = None
    if round_trip:
        back = search_flights(destination, source, end.isoformat(), prefer_flight)
        return_flight = back["cheapest"] if prefer_flight == "price" else back["fastest"]
        if return_flight:
            flight_cost += return_flight["price"] * travelers
            why.append(f"Return: {return_flight['airline']} (₹{return_flight['price']:,}).")
        else:
            why.append("No return flight found in the dataset; budget is one-way.")

    # --- Hotel (respect budget if given)
    max_price = None
    if budget and nights:
        remaining = budget - flight_cost - daily_expense * num_days * travelers
        if remaining > 0:
            max_price = remaining / (nights * rooms)
    hotels = search_hotels(destination, min_stars, max_price)
    if not hotels and max_price:
        why.append("No hotel fits the budget; showing best value regardless of budget.")
        hotels = search_hotels(destination, min_stars)
    if not hotels and min_stars:
        why.append(f"No {min_stars}+ star hotel found; relaxed star filter.")
        hotels = search_hotels(destination, 0)
    hotel = hotels[0] if hotels else None
    if hotel:
        why.append(f"Hotel: {hotel['name']} has the best stars-per-rupee "
                   f"({hotel['stars']}★ at ₹{hotel['price_per_night']:,}/night).")

    # --- Weather
    weather = get_weather(destination, start, end)

    # --- Itinerary
    places = search_places(destination, preferred_types) or search_places(destination)
    per_day = 3 if len(places) >= num_days * 3 else 2
    itinerary = []
    for i in range(num_days):
        stops = places[i * per_day:(i + 1) * per_day]
        notes = []
        if i == 0:
            notes.append("Arrive, check in and settle")
        if i == num_days - 1 and num_days > 1:
            notes.append("Check out and depart")
        if not stops:
            notes.append("Leisure day: local cafés, shopping, relaxed exploring")
        itinerary.append({
            "day": i + 1, "date": (start + timedelta(i)).isoformat(),
            "places": stops, "notes": notes,
            "weather": weather[i] if i < len(weather) else None,
        })
    why.append(f"Itinerary: top-rated {', '.join(preferred_types) if preferred_types else 'all-type'} "
               f"attractions in {destination}, {per_day} per day.")

    # --- Budget
    cost = estimate_budget(flight_cost, hotel["price_per_night"] if hotel else 0,
                           nights, daily_expense, travelers)
    within = None if not budget else cost["total"] <= budget
    if budget:
        why.append(f"Total ₹{cost['total']:,.0f} is "
                   f"{'within' if within else 'OVER'} your budget of ₹{budget:,.0f}.")

    return {
        "summary": {"title": f"Your {num_days}-Day Trip to {destination}",
                    "from": source, "to": destination, "start": start.isoformat(),
                    "end": end.isoformat(), "travelers": travelers, "rooms": rooms},
        "flight": _flight_summary(flight),
        "return_flight": _flight_summary(return_flight) if return_flight else None,
        "hotel": hotel, "itinerary": itinerary, "budget": cost,
        "within_budget": within, "reasoning": why,
    }


def render_markdown(plan: dict) -> str:
    """Human-readable version of a plan."""
    s, f, h, b = plan["summary"], plan["flight"], plan["hotel"], plan["budget"]
    L = [f"# {s['title']} ({s['start']} → {s['end']})",
         f"*{s['travelers']} traveler(s), from {s['from']}*", "", "### Flight Selected"]
    for leg in f["legs"]:
        L.append(f"- {f['airline']} (₹{f['price_per_person']:,}) – {leg['from']} → {leg['to']}, "
                 f"departs {leg['departs'][11:16]}")
    if plan["return_flight"]:
        r = plan["return_flight"]
        L.append(f"- Return: {r['airline']} (₹{r['price_per_person']:,})")
    L += ["", "### Hotel Recommendation"]
    L.append(f"- {h['name']} (₹{h['price_per_night']:,}/night, {h['stars']}-star, "
             f"{', '.join(h['amenities'])})" if h else "- No hotel available")
    L += ["", "### Weather & Itinerary"]
    for d in plan["itinerary"]:
        w = d["weather"] or {}
        temp = f" ({w['temp_max_c']}°C)" if "temp_max_c" in w else ""
        L.append(f"**Day {d['day']} ({d['date']})** – {w.get('summary', 'n/a')}{temp}")
        L += [f"- {p['name']} ({p['type']}, ⭐{p['rating']})" for p in d["places"]]
        L += [f"- {n}" for n in d["notes"]]
    L += ["", "### Estimated Total Budget",
          f"- Flight: ₹{b['flight']:,.0f}", f"- Hotel: ₹{b['hotel']:,.0f}",
          f"- Food & Travel: ₹{b['food_and_local_travel']:,.0f}", "---",
          f"**Total Cost: ₹{b['total']:,.0f}**", "", "### Why we selected this"]
    L += [f"- {r}" for r in plan["reasoning"]]
    return "\n".join(L)
