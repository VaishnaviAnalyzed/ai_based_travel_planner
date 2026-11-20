"""Command-line interface: python cli.py Delhi Goa 2026-12-12 3 [--agent "query"]"""
import argparse
import json

from planner import plan_trip, render_markdown

p = argparse.ArgumentParser(description="Travel planning assistant")
p.add_argument("source"); p.add_argument("destination")
p.add_argument("start_date", help="YYYY-MM-DD"); p.add_argument("days", type=int)
p.add_argument("--travelers", type=int, default=1)
p.add_argument("--budget", type=float)
p.add_argument("--types", nargs="*")
p.add_argument("--round-trip", action="store_true")
p.add_argument("--json", action="store_true", help="print raw JSON")
a = p.parse_args()
plan = plan_trip(a.source, a.destination, a.start_date, a.days, a.travelers,
                 a.budget, preferred_types=a.types, round_trip=a.round_trip)
print(json.dumps(plan, indent=2, ensure_ascii=False) if a.json else render_markdown(plan))
 