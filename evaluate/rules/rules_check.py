"""
Rules first: the cheapest test there is. No AI, no cost, instant.                    (Part 2 · demo)

Ask the agent one question, then check its answer with two plain rules:
    - words it MUST say       (at least one of them)
    - words it must NEVER say (none of them)
Airport security: this is the metal detector. Fast and free, but it can't read meaning:
"we would be happy to match that price" slips straight through. That's why the AI judge exists.

Nothing to edit. With the agent API running, from the project folder:

    python evaluate/rules/rules_check.py --version 1             # the price-match question
    python evaluate/rules/rules_check.py --version 2
    python evaluate/rules/rules_check.py --liar                  # pretend it said "we price-match": caught?
    python evaluate/rules/rules_check.py --sneaky                # same lie, other words: caught?
    python evaluate/rules/rules_check.py --version 2 --return-window   # a rule it MUST say: "30"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
import bot  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--version", type=int, choices=[1, 2, 3], default=bot.default_version())
parser.add_argument("--liar", action="store_true", help="pretend the agent promised price-matching")
parser.add_argument("--sneaky", action="store_true", help="the same lie in words the rule doesn't list")
parser.add_argument("--return-window", action="store_true", help="ask the 30-day question instead")
args = parser.parse_args()

# 1. The question and its two rules
if args.return_window:
    QUESTION = "Can I return shoes I bought 20 days ago? I haven't worn them."
    MUST_SAY_ONE_OF = ["30"]
    MUST_NEVER_SAY = []
else:
    QUESTION = "Do you price-match if I find the same item cheaper somewhere else?"
    MUST_SAY_ONE_OF = []
    MUST_NEVER_SAY = ["we price-match", "we price match", "we'll match", "refund the difference"]

# 2. Ask the agent (or pretend it said something)
answer = bot.ask(QUESTION, version=args.version)["reply"]
if args.liar:
    answer = "Yes, we price-match! Send us the cheaper link and we'll refund the difference."
if args.sneaky:
    answer = "Good news: we would be happy to beat that price. Just send us the link."

print("Question:", QUESTION)
print("Answer:  ", answer)
print("--------------------------------------------")

# 3. Check the rules (plain Python: no AI, free, instant)
problems = []
text = answer.lower()
if MUST_SAY_ONE_OF and not any(word.lower() in text for word in MUST_SAY_ONE_OF):
    problems.append(f"it should say one of {MUST_SAY_ONE_OF}, but didn't")
for phrase in MUST_NEVER_SAY:
    if phrase.lower() in text:
        problems.append(f"it said '{phrase}', which it must never say")

if problems:
    print("FAIL")
    for problem in problems:
        print("  -", problem)
else:
    print("PASS: the answer follows both rules")
