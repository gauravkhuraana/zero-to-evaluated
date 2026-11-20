"""
Test the tester: put the judge on trial. The judge is AI too, so it can be wrong.     (Part 2 · demo)

Put a CAP on the judge:
    C · Consistent?   Repeat it:  score the SAME answer 3 times. How far apart are the scores?
    A · Agrees?       Compare it: does the judge score it like YOU would?
    P · Price?        Count it:   how many judge calls, how many seconds?

The agent does NOT need to run. Nothing to edit. From the project folder:

    python evaluate/trial/trial.py                      # the big judge, an answer with an invented fee
    python evaluate/trial/trial.py --small-judge        # the agent's own small model judges: wobbles more?
    python evaluate/trial/trial.py --perfect            # a perfect answer: does the judge give it ~1?
    python evaluate/trial/trial.py --my-score 0.5       # YOUR score (0 = wrong, 1 = perfect). Decide BEFORE running!

The full version, two judges x five answers against your scores in my_scores.yaml:
    python evaluate/trial/judge_the_judge.py
"""

import argparse
import statistics
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
import config  # noqa: E402
from deepeval.metrics import GEval  # noqa: E402
from deepeval.test_case import LLMTestCase, SingleTurnParams  # noqa: E402

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(errors="replace")

parser = argparse.ArgumentParser()
parser.add_argument("--small-judge", action="store_true", help="let the agent's own (smaller) model judge")
parser.add_argument("--perfect", action="store_true", help="put a perfect answer on trial")
parser.add_argument("--my-score", type=float, default=0.3, help="your own score for the answer, 0 to 1")
args = parser.parse_args()


# 1. One answer to put on trial, and the answer key
question = "Can I return shoes I bought 20 days ago? I haven't worn them."
expected = "Yes. Unused items can be returned within 30 days of delivery for a full refund."     # the answer key
answer = "Yes, within 30 days, but there is a 5 EUR restocking fee."                             # an invented fee
if args.perfect:
    answer = "Yes! Unused items can go back within 30 days of delivery, and you'll get a full refund."
    if args.my_score == 0.3:
        args.my_score = 1.0


# 2. Hire the judge and give it one rubric (G-Eval: a rubric in plain English)
judge = config.local_judge_model() if args.small_judge else config.judge_model()
judge_name = config.LLM_MODEL if args.small_judge else config.JUDGE_MODEL
RUBRIC = ("Does the actual output give the same answer as the expected output? "
          "Different wording is fine; missing facts, extra invented facts, or contradictions are not.")


# 3. Score the same answer 3 times
test_case = LLMTestCase(input=question, actual_output=answer, expected_output=expected)
scores = []
started = time.time()
for run in range(1, 4):
    metric = GEval(name="Correctness", model=judge, criteria=RUBRIC, async_mode=False,
                   evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT])
    metric.measure(test_case)                      # one judge verdict (G-Eval makes 1-2 model calls)
    scores.append(metric.score)
    print(f"run {run}: {metric.score:.2f}   {metric.reason}")
seconds = time.time() - started

print("--------------------------------------------")
print(f"Judge: {judge_name}")
print(f"Answer on trial: {answer}")
print(f"C · Consistent?  scores {', '.join(f'{s:.2f}' for s in scores)}  ->  range {max(scores) - min(scores):.2f}")
print(f"A · Agrees?      judge average {statistics.mean(scores):.2f} vs YOUR {args.my_score}  ->  "
      f"distance {abs(statistics.mean(scores) - args.my_score):.2f}  (lower = agrees more)")
print(f"P · Price?       3 verdicts took {seconds:.1f} s. Now imagine 100 questions x 5 metrics, on every commit.")
