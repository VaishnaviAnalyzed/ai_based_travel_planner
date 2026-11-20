"""Streamlit front end: form-based planner + natural-language LangChain agent."""
import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from config import CITY_COORDS, DEFAULT_DAILY_EXPENSE
from planner import plan_trip, render_markdown
from tools import list_place_types

st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
st.title("✈️ Agentic AI Travel Planning Assistant")
CITIES = sorted(CITY_COORDS)
ALL_TYPES = sorted({t for c in CITIES for t in list_place_types(c)})

tab_form, tab_agent = st.tabs(["🧭 Plan with filters", "🤖 Ask the AI agent"])

with tab_form:
    c1, c2, c3 = st.columns(3)
    source = c1.selectbox("From", CITIES, index=CITIES.index("Delhi"))
    dest = c2.selectbox("To", CITIES, index=CITIES.index("Kolkata"))
    start = c3.date_input("Start date", date.today() + timedelta(days=30))
    c4, c5, c6 = st.columns(3)
    days = c4.slider("Trip length (days)", 3, 7, 3)
    travelers = c5.number_input("Travelers", 1, 10, 1)
    budget = c6.number_input("Max budget ₹ (0 = none)", 0, 1_000_000, 0, step=1000)
    c7, c8, c9 = st.columns(3)
    stars = c7.slider("Min hotel stars", 0, 5, 3)
    daily = c8.number_input("Food & local travel ₹/day/person", 0, 20000,
                            DEFAULT_DAILY_EXPENSE, step=100)
    prefer = c9.radio("Flight preference", ["price", "duration"],
                      format_func=lambda x: "Cheapest" if x == "price" else "Fastest",
                      horizontal=True)
    types = st.multiselect("Interests (place types)", ALL_TYPES)
    round_trip = st.checkbox("Include return flight")

    if st.button("Generate itinerary", type="primary"):
        if source == dest:
            st.error("Source and destination must differ.")
        else:
            try:
                with st.spinner("Calling tools…"):
                    plan = plan_trip(source, dest, start, days, travelers, budget or None,
                                     stars, types, daily, round_trip, prefer)
                st.session_state["plan"] = plan
            except ValueError as exc:
                st.error(str(exc))

    plan = st.session_state.get("plan")
    if plan:
        b = plan["budget"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Flight", f"₹{b['flight']:,.0f}")
        m2.metric("Hotel", f"₹{b['hotel']:,.0f}")
        m3.metric("Food & travel", f"₹{b['food_and_local_travel']:,.0f}")
        m4.metric("Total", f"₹{b['total']:,.0f}")
        if plan["within_budget"] is False:
            st.warning("Estimated total exceeds your budget.")
        left, right = st.columns([2, 1])
        with left:
            st.markdown(render_markdown(plan))
        with right:
            st.subheader("Cost split")
            st.bar_chart(pd.Series({"Flight": b["flight"], "Hotel": b["hotel"],
                                    "Food & travel": b["food_and_local_travel"]}))
            st.subheader("Temperatures")
            rows = [{"date": d["date"], "max °C": d["weather"].get("temp_max_c"),
                     "min °C": d["weather"].get("temp_min_c")}
                    for d in plan["itinerary"] if d["weather"]]
            if rows:
                st.line_chart(pd.DataFrame(rows).set_index("date"))
        st.download_button("⬇ Download JSON", json.dumps(plan, indent=2, ensure_ascii=False),
                           "itinerary.json", "application/json")
        with st.expander("Raw JSON"):
            st.json(plan)

with tab_agent:
    st.write("Describe your trip; the LangChain agent decides which tools to call.")
    query = st.text_area("Your request", height=110,
                         placeholder="Plan a 4-day trip from Delhi to Kolkata starting "
                                     "2026-12-10, budget ₹30,000, I like temples and museums.")
    if st.button("Run agent", type="primary") and query.strip():
        try:
            from agent import run_agent
            with st.spinner("Agent reasoning and calling tools…"):
                answer, steps = run_agent(query)
            st.markdown(answer)
            with st.expander(f"Agent tool calls ({len(steps)})"):
                for name, args in steps:
                    st.code(f"{name}({json.dumps(args, ensure_ascii=False)})", language="python")
        except Exception as exc:  # LLM unavailable -> show real error + fallback
            import os
            st.error(f"LLM agent failed (provider: {os.getenv('OPENAI_BASE_URL') or 'OpenAI'}, "
                     f"model: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}): {exc}")
            st.info("Using the built-in planner (same tools, no LLM) for your request instead.")
            try:
                from nl_parser import parse_request
                params = parse_request(query)
                fallback = plan_trip(**params)
                st.markdown(render_markdown(fallback))
                with st.expander("Parsed request"):
                    st.json(params)
            except ValueError as err:
                st.warning(str(err))
