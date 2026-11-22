"""
STEP 4b · AI tests AI: an LLM judge scores the agent's answers

We can't compare words, so we compare MEANING. A second, bigger LLM (the "judge") reads
the question, the agent's answer and the facts, and gives a score from 0 to 1 with a reason.
DeepEval gives us ready-made judges ("metrics"):

    Relevance       AnswerRelevancyMetric   does the answer actually answer the question?
    Groundedness    FaithfulnessMetric      is every claim backed by the policy pages the agent found?
    Hallucination   HallucinationMetric     does the answer contradict what we KNOW is true?
    Accuracy        GEval "Correctness"     does it say the same as our expected answer?

Each metric has a pass mark (threshold). Below it, the test fails, and DeepEval tells you why.

Run it (from the project folder, with .venv active):
    pytest step4_judge/test_answers.py -v
"""
import os

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval, HallucinationMetric
from deepeval.models import LocalModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv

from step2_agent.agent import ask_agent

load_dotenv()

# 1. The judge: a bigger LLM than the agent uses (JUDGE_* settings in .env)
judge = LocalModel(
    model=os.getenv("JUDGE_MODEL"),
    base_url=os.getenv("JUDGE_BASE_URL"),
    api_key=os.getenv("JUDGE_API_KEY"),
)

# 2. Our test cases: a question + what we KNOW the right answer is.
#    Add your own! Copy one line and change the question and the expected answer.
GOLDEN_QUESTIONS = [
    ("How many days do I have to return an item?",
     "Unused items can be returned within 30 days of delivery for a full refund."),
    ("Can I return something I bought in the clearance sale?",
     "No. Clearance items are final sale and cannot be returned, unless they arrived damaged."),
    ("Do you price-match if I find it cheaper somewhere else?",
     "The policy does not mention price matching, so the agent should say it doesn't know."),
]


# 3. One test per question. pytest runs the function once for each (question, expected) pair.
@pytest.mark.parametrize("question, expected", GOLDEN_QUESTIONS)
def test_answer_quality(question, expected):

    # Ask the agent (step 2). It returns its answer AND the policy pages it read.
    result = ask_agent(question)
    print("Agent's answer:", result["answer"])

    # Put everything the judge needs into one test case
    test_case = LLMTestCase(
        input=question,
        actual_output=result["answer"],
        expected_output=expected,               # for Accuracy
        context=[expected],                     # for Hallucination: what we KNOW is true
        retrieval_context=result["policy_pages"],   # for Groundedness: what the agent read
    )

    # The four judges, each with a pass mark
    relevance = AnswerRelevancyMetric(model=judge, threshold=0.7)
    groundedness = FaithfulnessMetric(model=judge, threshold=0.7)
    hallucination = HallucinationMetric(model=judge, threshold=0.5)   # here LOWER is better
    accuracy = GEval(
        name="Correctness",
        criteria="Does the actual output say the same thing as the expected output? Different words are fine.",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        model=judge,
        threshold=0.6,
    )

    # Fails if ANY judge scores below its pass mark, and prints every score + reason
    assert_test(test_case, [relevance, groundedness, hallucination, accuracy])
