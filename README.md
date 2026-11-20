# Agentic AI-Based Travel Planning Assistant (LangChain)

Plans 3–7 day trips from flights, hotels and places JSON datasets plus live
Open-Meteo weather, using a LangChain tool-calling agent and a Streamlit UI.

## Structure
```
app.py            Streamlit UI (filter form + AI agent tab)
agent.py          LangChain tools + tool-calling AgentExecutor
planner.py        Deterministic tool-chaining planner (JSON + markdown, reasoning)
cli.py            Command-line interface
config.py         Paths, city coordinates, defaults
data_loader.py    JSON loading / error handling
tools/            flights, hotels, places, weather, budget
data/             flights.json, hotels.json, places.json
tests/            pytest suite
```

## Setup
```
pip install -r requirements.txt
cp .env.example .env      # add OPENAI_API_KEY (only needed for the agent tab; model and provider are set in .env)
streamlit run app.py
python cli.py Delhi Kolkata 2026-12-12 3 --budget 25000 --types temple museum
python -m pytest
```

## How it works
Tools: Flight Search (cheapest/fastest, one-stop fallback), Hotel Recommendation
(city/stars/price, best value), Places Discovery (type & rating), Weather Lookup
(Open-Meteo forecast; historical same-date data when the trip is >16 days away),
Budget Estimation (flight + hotel × nights + daily expenses).
The agent (ReAct-style tool calling) decides the call order, builds the itinerary
and explains why each option was chosen.

## Data notes
- Sample flights are dated 2025 and cover only some routes; if the exact date or
  a direct route is missing, the nearest route option / one-stop connection is used and flagged.
- Hotels have stars (no rating); "best value" = stars per rupee.
- Nights = days − 1; one room per 2 travelers.
