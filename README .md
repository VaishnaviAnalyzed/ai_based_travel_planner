# ✈️ Agentic AI-Based Travel Planning Assistant

An intelligent travel planner built with **LangChain** and **Streamlit**. Give it a
request such as *"4-day trip from Delhi to Jaipur starting 2026-12-15, budget ₹30,000,
I like forts and temples"* and a ReAct-style agent decides which tools to call, then
returns a complete itinerary with flights, hotel, weather, budget and the reasoning
behind each choice, as readable text and JSON.

## Problem Statement
Planning a trip means switching between many websites to compare flights, hotels and
attractions while keeping time, budget, weather and preferences in mind. This project
automates that with an AI agent that reasons like a travel expert.

## Features
- **LangChain agent** that autonomously picks and chains tools (works with Gemini, OpenAI, Groq or any OpenAI-compatible model)
- **Five tools:** flight search, hotel recommendation, places discovery, live weather, budget estimation
- **Filtering and ranking:** cheapest or fastest flight, best-value hotel, top-rated places
- **Explainable decisions:** a "Why we selected this" section in every plan
- **Dual output:** human-readable markdown and clean JSON (downloadable)
- **Streamlit UI** with filters, charts and an AI agent tab, plus a **CLI**
- **Built-in planner** that works without any LLM or API key
- Retries and fallback models when the LLM is overloaded

## Tech Stack
Python · LangChain · Streamlit · Open-Meteo API · JSON datasets · pytest

## Project Structure
```
travel_planner/
├── app.py            # Streamlit UI (filter form + AI agent tab)
├── agent.py          # LangChain tools + agent (ReAct / tool-calling)
├── planner.py        # Rule-based planner: chains tools, JSON + markdown, reasoning
├── nl_parser.py      # Parses free text for the no-LLM fallback
├── cli.py            # Command-line interface
├── config.py         # Paths, city coordinates, defaults
├── data_loader.py    # JSON loading and error handling
├── tools/
│   ├── flights.py    # Flight Search Tool
│   ├── hotels.py     # Hotel Recommendation Tool
│   ├── places.py     # Places Discovery Tool
│   ├── weather.py    # Weather Lookup Tool (Open-Meteo)
│   └── budget.py     # Budget Estimation Tool
├── data/             # flights.json, hotels.json, places.json
├── tests/            # pytest unit tests
├── requirements.txt
└── .env.example
```

## Setup
```bash
git clone <your-repo-url>
cd travel_planner
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

### Configure the LLM (only needed for the AI agent tab)
Copy `.env.example` to a file named exactly `.env` and fill it in.

**Google Gemini (free tier)**
```
OPENAI_API_KEY=your_gemini_key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-3.8-flash
```
**Groq (free tier)**
```
OPENAI_API_KEY=your_groq_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```
**OpenAI**
```
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-4o-mini
```
Optional: `LLM_FALLBACK_MODELS=model-a,model-b` (tried if the main model is overloaded) and
`AGENT_MODE=tools` (native function calling; default is the text-based ReAct agent that
works with every provider). Model names change over time, so check your provider's model list.

> Never commit `.env`. Add it to `.gitignore`.

## Usage
```bash
streamlit run app.py                                   # web app
python cli.py Delhi Kolkata 2026-12-12 3 --budget 25000 --types temple museum
python cli.py Delhi Jaipur 2026-12-15 4 --json         # raw JSON output
python -m pytest                                       # run tests
```
- **Plan with filters tab:** choose cities, dates, days, budget, hotel stars and interests. No LLM needed.
- **Ask the AI agent tab:** describe the trip in plain English. If the LLM is unavailable, the built-in planner handles the request instead.

## Example Output
```
Your 3-Day Trip to Kolkata (2026-12-12 → 2026-12-14)

Flight Selected:  Air India (₹3,779) – Delhi → Kolkata
Hotel:            Grand Palace Hotel (₹2,554/night, 3-star)
Weather:          Day 1: Sunny (27°C) ...
Itinerary:        Day 1: Historic Temple, Scenic Museum ...
Estimated Total:  Flight + Hotel + Food & Travel = ₹xx,xxx
```

## How It Works
1. The agent reads the request and decides which tools to call.
2. **Flights:** filter by route and date, then pick the cheapest or fastest (one-stop fallback if there is no direct flight).
3. **Hotels:** filter by city, stars and price, ranked by stars per rupee.
4. **Places:** filter by type and rating, best rated first.
5. **Weather:** Open-Meteo live forecast for trips within 16 days; historical same-date data for later trips.
6. **Budget:** flight + hotel × nights + daily food and local travel.
7. The agent assembles the itinerary and explains its choices.

## Data Notes
- Datasets cover 8 cities: Delhi, Mumbai, Goa, Bangalore, Chennai, Hyderabad, Kolkata, Jaipur.
- Sample flights are dated 2025 and cover only some routes. If the exact date or a direct route is missing, the closest option or a one-stop connection is used and flagged in the plan.
- Hotels have star ratings (no review score), so "best value" means stars per rupee.
- Nights = days − 1; one room per 2 travelers.

## Future Improvements
Real flight/hotel APIs, round-trip date matching, map view of attractions, booking links, multi-city trips.
