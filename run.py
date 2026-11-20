"""
Run any agent version from the terminal and read its flight recorder.        (Part 1 · Exercises 1 and 2)

    python run.py --version 1 1043                       # a seeded order: uses that order's demo message
    python run.py --version 2 "Do you price-match?"      # or type the customer's message yourself
    python run.py --version 3 all                        # all 10 seeded orders
    python run.py --compare "Can I return a clearance item?"    # the same message to v1, v2 and v3

No --version? You get AGENT_VERSION from .env (default 3).
Nothing to edit in this file.
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "agent"))
import config  # noqa: E402

sys.stdout.reconfigure(errors="replace")    # Windows consoles can't print every character a model uses

ORDERS = {o["order_id"]: o for o in json.loads((config.DATA_DIR / "orders.json").read_text(encoding="utf-8"))}


def load(version):
    if version == 1:
        import v1_agent as agent
    elif version == 2:
        import v2_agent as agent
    else:
        import v3_crew as agent
    return agent


def show(version, message):
    print(f"\n=== v{version} · customer: {message}")
    result = load(version).run_agent(message)

    for step in result["steps"]:
        kind = step["type"]
        if kind == "review":
            detail = ("APPROVED: " if step["approved"] else "SENT BACK: ") + step["reason"]
        elif kind in ("tool_result", "plan"):
            detail = (step.get("name", "") + " " + str(step["content"]).replace("\n", " "))[:100]
        elif kind == "reply":
            detail = ""
        else:
            detail = step.get("name", "") + " " + json.dumps(step.get("args", ""))
        print(f"  {step.get('agent', ''):<17} {kind:<11} {detail}")

    print(f"  -> outcome: {result['outcome']}")
    if result.get("sources"):
        print(f"  -> pages it read: {result['sources']}")
    print(f"  customer sees: {result['reply']}")


def main():
    parser = argparse.ArgumentParser(description="Run a ShopKart agent version.")
    parser.add_argument("--version", type=int, choices=[1, 2, 3], default=int(os.getenv("AGENT_VERSION", "3")))
    parser.add_argument("--compare", action="store_true", help="send the same message to v1, v2 and v3")
    parser.add_argument("what", nargs="+", help="an order id (e.g. 1043), 'all', or the customer's message")
    args = parser.parse_args()

    text = " ".join(args.what)
    if text == "all":
        messages = [order["demo_message"] for order in ORDERS.values()]
    elif text in ORDERS:
        messages = [ORDERS[text]["demo_message"]]
    else:
        messages = [text]

    versions = [1, 2, 3] if args.compare else [args.version]
    for message in messages:
        for version in versions:
            show(version, message)


if __name__ == "__main__":
    main()
