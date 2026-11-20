"""LangChain tool-calling agent that autonomously plans trips."""
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool

from config import DEFAULT_DAILY_EXPENSE
from tools import (estimate_budget, get_weather, search_flights,
                   search_hotels, search_places)

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH, override=True)


def _dump(obj) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)


@tool
def flight_search(source: str, destination: str, date: str = "",
                  sort_by: str = "price") -> str:
    """Search flights between two cities. date is YYYY-MM-DD (optional).
    sort_by is 'price' or 'duration'. Returns options plus cheapest and fastest."""
    return _dump(search_flights(source, destination, date or None, sort_by))


@tool
def hotel_search(city: str, min_stars: int = 0, max_price_per_night: float = 0) -> str:
    """Find hotels in a city. min_stars filters quality; max_price_per_night
    (0 = no limit) filters price. Results are sorted by best value."""
    return _dump(search_hotels(city, min_stars, max_price_per_night or None))


@tool
def places_search(city: str, types: str = "", min_rating: float = 0.0) -> str:
    """Find attractions in a city. types is a comma-separated list such as
    'beach,temple,museum,fort,park,market,lake,monument' (empty = all)."""
    kinds = [t.strip() for t in types.split(",") if t.strip()]
    return _dump(search_places(city, kinds, min_rating))


@tool
def weather_lookup(city: str, start_date: str, end_date: str) -> str:
    """Daily weather for a city (YYYY-MM-DD dates) from Open-Meteo."""
    return _dump(get_weather(city, start_date, end_date))


@tool
def budget_estimate(flight_cost: float, hotel_price_per_night: float, nights: int,
                    daily_expense: float = DEFAULT_DAILY_EXPENSE,
                    travelers: int = 1) -> str:
    """Estimate total trip cost: flights + hotel nights + daily food/local travel."""
    return _dump(estimate_budget(flight_cost, hotel_price_per_night, nights,
                                 daily_expense, travelers))


TOOLS = [flight_search, hotel_search, places_search, weather_lookup, budget_estimate]

BASE_PROMPT = """You are an expert travel planning agent. Today is {today}.
Cities in the data (ONLY these are supported): Delhi, Mumbai, Goa, Bangalore, Chennai,
Hyderabad, Kolkata, Jaipur. If the user asks for another place (e.g. Kyoto), say it is not
supported and suggest the closest supported city instead of calling tools for it.
If the departure city or destination is missing, ask the user instead of guessing.
Prices are in INR. Nights = days - 1.

Workflow: (1) flight_search for the route (and return if asked), (2) hotel_search,
(3) places_search, (4) weather_lookup for the travel dates, (5) budget_estimate.
Respect any budget, star or interest preference. If the dataset has no flight on
the exact date, use the closest option and say so. Never invent data; use only tool output.

Final answer format (markdown):
# Your N-Day Trip to X (dates)
### Flight Selected / ### Hotel Recommendation / ### Weather & Itinerary (day-wise,
with weather per day) / ### Estimated Total Budget (flight, hotel, food & travel, total)
/ ### Why we selected this."""

# Text-based JSON tool protocol: works with ANY chat model (Gemini, Groq, OpenAI...)
# and avoids provider-specific native function-calling quirks (e.g. Gemini 3
# "thought_signature" errors).
REACT_RULES = """

You have access to these tools:

{tools}

Use a JSON blob to call ONE tool at a time, with keys "action" (tool name) and
"action_input" (a JSON object of the tool's arguments). Valid "action" values:
"Final Answer" or {tool_names}

Format:
Thought: reasoning about what to do next
Action:
```
{{
  "action": "$TOOL_NAME",
  "action_input": {{"arg": "value"}}
}}
```
Observation: tool result (provided to you)
... (repeat Thought/Action/Observation as needed)
Thought: I have everything I need
Action:
```
{{
  "action": "Final Answer",
  "action_input": "the full markdown answer as one string (use \\n for new lines)"
}}
```
Always reply with exactly one valid JSON blob after "Action:"."""


def build_agent(model: str = None, api_key: str = None):
    """Create the AgentExecutor (needs an OpenAI-compatible API key).

    AGENT_MODE=react (default) uses a structured-chat ReAct agent;
    AGENT_MODE=tools uses native function calling (OpenAI models).
    """
    from langchain.agents import (AgentExecutor, create_structured_chat_agent,
                                  create_tool_calling_agent)
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI

    load_dotenv(ENV_PATH, override=True)  # re-read so edits apply without restart
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key or key.startswith(("your-key", "PASTE_")):
        raise RuntimeError(f"OPENAI_API_KEY is not set. Create the file {ENV_PATH} "
                           "(copy .env.example, name it exactly '.env') and add your key.")
    llm = ChatOpenAI(model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0,
                     api_key=key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    base = BASE_PROMPT.replace("{today}", date.today().isoformat())

    if os.getenv("AGENT_MODE", "react").lower() == "tools":
        prompt = ChatPromptTemplate.from_messages([
            ("system", base), ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")])
        agent = create_tool_calling_agent(llm, TOOLS, prompt)
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", base + REACT_RULES),
            ("human", "{input}\n\n{agent_scratchpad}\n(reply with one JSON blob)")])
        agent = create_structured_chat_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, max_iterations=12,
                         return_intermediate_steps=True, handle_parsing_errors=True)


def run_agent(query: str, model: str = None, api_key: str = None):
    """Run the agent. Returns (final_text, [(tool_name, tool_input), ...])."""
    result = build_agent(model, api_key).invoke({"input": query})
    steps = [(a.tool, a.tool_input) for a, _ in result["intermediate_steps"]]
    return result["output"], steps
