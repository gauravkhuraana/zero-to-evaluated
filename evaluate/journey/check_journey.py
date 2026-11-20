"""
Right answer, wrong journey: check the PATH, not just the landing.                  (Part 2 · Exercise 4)

Three parts:
    1. Send one customer message to the crew (version 3) over POST /chat
    2. Read the flight recorder: every step, which agent, which tool, which arguments, in which order
    3. Check it: the outcome, the tool order, the hand-over to the Reviewer, the amount

No AI judge needed here: a tool call is just data, and data is something we can assert on.
Check E does the same "right tools, right order" check with a ready-made DeepEval agent metric.

Nothing to edit. With the agent API running, from the project folder:

    python evaluate/journey/check_journey.py              # healthy crew: all PASS

Then plant ONE known bug in the REAL crew and run the same script again. Predict first: which check fails?

    python plant_bug.py skip_lookup      # the refund happens BEFORE the order lookup
    python evaluate/journey/check_journey.py
    python plant_bug.py overpay          # the payment step pays double
    python evaluate/journey/check_journey.py
    python plant_bug.py off              # ALWAYS finish with this: healthy crew again

The running API notices the bug switch by itself: no restart needed.
"""

import json
import os
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
import bot  # noqa: E402
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.models import LocalModel
from deepeval.test_case import LLMTestCase, ToolCall

warnings.filterwarnings("ignore")
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")


# 1. Send one customer message to the crew (version 3)

message = "My headphones from order 1043 arrived broken, refund please."
PRICE_PAID = 49.0          # what the customer paid for order 1043 (shared/data/orders.json)

result = bot.ask(message, version=3)      # the crew

# 2. Read the flight recorder

print("Customer:", message)
print("Reply:   ", result["reply"])
print("Outcome:")
print(json.dumps(result["outcome"], indent=2))
print("Flight recorder:")
for step_number, step in enumerate(result["steps"], start=1):
    print(f"Step {step_number}:")
    print(json.dumps(step, indent=2))
print("--------------------------------------------")

tools = []
reviews = []

for step in result["steps"]:
    if step["type"] in ("tool_call", "proposal"):
        tools.append(step["name"])

    if step["type"] == "review":
        reviews.append(step)


# 3. Check it

checks = {}

# Check A · The landing: did the customer get the right outcome?
action = result["outcome"]["action"]
checks["right outcome (refund)"] = action == "refund"

# Check B · The baton: did the Reviewer SEE the order facts, or approve blind?
reviewer_saw_the_facts = bool(reviews)

for review in reviews:
    review_input = review["input"]
    has_order_number = "1043" in review_input
    has_order_details = "price_paid" in review_input
    reviewer_saw_the_facts = reviewer_saw_the_facts and has_order_number and has_order_details

checks["reviewer saw the facts"] = reviewer_saw_the_facts

# Check C · The journey: "get_order" must come BEFORE "issue_refund"
refund_was_proposed = "issue_refund" in tools
order_was_looked_up = "get_order" in tools

if refund_was_proposed and order_was_looked_up:
    lookup_position = tools.index("get_order")
    refund_position = tools.index("issue_refund")
    looked_up_before_refunding = lookup_position < refund_position
else:
    looked_up_before_refunding = not refund_was_proposed

checks["looked up before refunding"] = looked_up_before_refunding

# Check D · The money: the amount that moved must be at most PRICE_PAID
amount_refunded = result["outcome"].get("amount", 0)
checks["no overpayment"] = amount_refunded <= PRICE_PAID

# Check E · The journey again, with a ready-made DeepEval agent metric: ToolCorrectnessMetric.
# Same question as check C ("right tools, right order?"), but DeepEval gives you the score AND the reason.
# It only compares two lists, so there is no AI call and no API key needed.
test_case = LLMTestCase(
    input=message,
    actual_output=result["reply"],
    tools_called=[ToolCall(name=name) for name in tools],                 # what the crew really did
    expected_tools=[ToolCall(name="get_order"), ToolCall(name="issue_refund")],   # what a good journey does
)

metric = ToolCorrectnessMetric(
    threshold=1.0,                       # 1.0 = every expected tool was called, in the right order
    should_consider_ordering=True,       # the order matters: look up BEFORE paying
    model=LocalModel(model="not-used", base_url="http://localhost", api_key="not-used"),   # required by the class, never called here
    async_mode=False,
)
metric.measure(test_case)
checks["DeepEval tool correctness"] = metric.is_successful()


# Results

for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")

print()
print(f"DeepEval ToolCorrectnessMetric: score {metric.score:.2f}")
print(f"  tools called:   {tools}")
print(f"  reason: {metric.reason}")


# ---------------------------------------------------------------------------
# THE AGENT METRICS MENU: assertions DeepEval gives you ready-made for AGENTS
# ---------------------------------------------------------------------------
# For a chatbot you asked: "is the answer true / grounded / relevant?"  (step 7)
# For an agent you ask:    "was the JOURNEY right?"  DeepEval has metrics for that too:
#
#   Metric                    The question it answers                            Needs the AI judge?
#   ------------------------  -------------------------------------------------  -------------------
#   ToolCorrectnessMetric     Right tools, in the right order?  (used above)     no
#   ArgumentCorrectnessMetric Right arguments given to each tool?                yes
#   ToolUseMetric             Picked the best tool from the ones available?      yes
#   TaskCompletionMetric      Did the agent finish what the user asked?          yes
#   PlanQualityMetric         Was the plan the agent wrote any good?             yes
#   PlanAdherenceMetric       Did it FOLLOW its own plan?                        yes
#   StepEfficiencyMetric      Any wasted or repeated steps?                      yes
#   AgentLoopDetectionMetric  Stuck going round in circles?                      no
#
# Same shape as every metric in this course: build it, call metric.measure(test_case), read score + reason.
# The ones with a judge also read the agent's recorded trace (DeepEval's @observe tracing).
# Rule of thumb from the top of this file: exact facts -> plain Python or ToolCorrectnessMetric (free, fast,
# repeatable); meaning -> a judge metric (slower, costs calls, and you put it on trial in step 9).
# More: https://deepeval.com/docs/metrics-introduction
