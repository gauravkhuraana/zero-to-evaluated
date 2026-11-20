"""
AI tests AI: a bigger model judges your agent's answers.                        (Part 2 · Exercise 3)

You can't assertEquals an answer that is worded differently every time. So we hire a judge:
a second, bigger model plus a ready-made rubric (a DeepEval "metric") that gives a score from 0 to 1,
a pass mark, and its reason.

    T · Truthful?          HallucinationMetric   does the answer contradict what we KNOW is true?
    U · Uses the source?   FaithfulnessMetric    is every claim backed by the policy pages the agent read?

Same questions, two agent versions. Before you run each one, predict: which version passes?

Nothing to edit. Keep the agent API running in another terminal (uvicorn agent.app:app --reload), then,
from the project folder with .venv active:

    python evaluate/judge/judge_answers.py --version 1      # tools, no policy: what does the judge say?
    python evaluate/judge/judge_answers.py --version 2      # + the policy book (RAG)
    python evaluate/judge/judge_answers.py --version 2 --liar     # pretend the agent lied: does the judge notice?
    python evaluate/judge/judge_answers.py --version 2 --all      # every judge question in golden_questions.yaml

Want it as a test suite with a scoreboard page?  pytest evaluate/judge --agent-version 1   (then 2)
"""

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
import bot  # noqa: E402
import config  # noqa: E402
import yaml  # noqa: E402
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric  # noqa: E402
from deepeval.test_case import LLMTestCase  # noqa: E402

warnings.filterwarnings("ignore")              # keep the output readable
sys.stdout.reconfigure(errors="replace")

GOLDEN = yaml.safe_load((config.ROOT / "evaluate" / "golden_questions.yaml").read_text(encoding="utf-8"))
QUICK = ["price-match", "clearance", "return-window"]       # three questions: not in policy, a trap, a plain one
LIAR = "Yes, we price-match! Send us the cheaper link and we'll refund the difference."

parser = argparse.ArgumentParser()
parser.add_argument("--version", type=int, choices=[1, 2, 3], default=bot.default_version())
parser.add_argument("--all", action="store_true", help="every question marked judge: true")
parser.add_argument("--liar", action="store_true", help="replace every answer with an invented price-match promise")
args = parser.parse_args()

cases = [c for c in GOLDEN if c.get("judge") and (args.all or c["id"] in QUICK)]
judge = config.judge_model()                    # the bigger model: JUDGE_* in .env

print(f"Agent version {args.version} · judge {config.JUDGE_MODEL} · {len(cases)} question(s)\n")
passed = 0
for case in cases:
    # 1. Get an answer from the agent, plus the policy pages it read (empty for v1: it has no book)
    result = bot.ask(case["question"], version=args.version)
    answer = LIAR if args.liar else result["reply"]
    pages = result["context"] or ["(the agent read no policy pages)"]

    # 2. Let the judge mark it against two rubrics
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=answer,
        context=[case["truth"]],        # what we KNOW is true (the answer key)  -> Truthful?
        retrieval_context=pages,        # what the agent read                    -> Uses the source?
    )
    metrics = [
        HallucinationMetric(model=judge, threshold=0.5, async_mode=False),
        FaithfulnessMetric(model=judge, threshold=0.7, async_mode=False),
    ]
    for metric in metrics:
        metric.measure(test_case)       # this is where the judge model is called

    # 3. Print the verdict
    ok = all(m.is_successful() for m in metrics)
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'}  {case['id']}")
    print(f"      Q: {case['question']}")
    print(f"      A: {answer}")
    for m in metrics:
        print(f"      {m.__name__:<14} {m.score:.2f} (pass mark {m.threshold})  {m.reason}")
    print()

print(f"v{args.version}: {passed} of {len(cases)} answers passed the judge.")
