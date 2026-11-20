"""Budget Estimation Tool: flight + hotel + per-day local expenses."""
import math

from config import DEFAULT_DAILY_EXPENSE


def estimate_budget(flight_cost: float, hotel_price_per_night: float, nights: int,
                    daily_expense: float = DEFAULT_DAILY_EXPENSE,
                    travelers: int = 1) -> dict:
    """Total trip cost in INR. Rooms = 1 per 2 travelers; flights/food per person."""
    rooms = math.ceil(travelers / 2)
    days = nights + 1
    hotel = hotel_price_per_night * nights * rooms
    local = daily_expense * days * travelers
    return {
        "flight": flight_cost, "hotel": hotel, "food_and_local_travel": local,
        "rooms": rooms, "travelers": travelers,
        "total": flight_cost + hotel + local,
    }
