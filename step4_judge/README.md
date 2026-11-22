# Step 4 · Why assertEquals fails, and what replaces it

**The idea:** an LLM never gives the same words twice, so `==` fails even when the answer is right.
So we compare **meaning** instead: a second, bigger LLM (the **judge**) scores each answer from 0 to 1 and gives its reason.

| We ask | DeepEval metric | It checks against |
|---|---|---|
| Relevance: does it answer the question? | `AnswerRelevancyMetric` | the question |
| Groundedness: is every claim backed by the policy? | `FaithfulnessMetric` | the pages the agent read |
| Hallucination: does it contradict the facts? | `HallucinationMetric` | what we know is true |
| Accuracy: is it the same as our expected answer? | `GEval` "Correctness" | our expected answer |

## Run it
This test is **supposed to fail**. Read the two answers in the output:
```bash
pytest step4_judge/test_assert_equals.py
```

Now let the judge score the agent's answers:
```bash
pytest step4_judge/test_answers.py -v
```

## Try these (15 minutes)
1. **Add your own question.** In `test_answers.py`, copy one line of `GOLDEN_QUESTIONS` and change the question and the expected answer. Run it again.
2. **Give a wrong expected answer** on purpose (for example "60 days" instead of 30). Which judges notice, and what reason do they give?
3. **Move a pass mark.** Change `threshold=0.7` to `0.95`. Do the tests still pass? What would *you* set it to for a real product?

## What to notice
- Every score comes with a **reason**. Read the reasons, not just the green or red.
- The judge is an LLM too, so it can be wrong. Would you trust it without checking a few scores yourself?
- Each test makes several judge calls, which costs time (and money on paid plans).
