# Take home: how to test an AI app, step by step

A checklist for your own team, from cheapest to most expensive. Start at the top, and only move down when you need to.

## 1 · Rules in code (free, instant, no AI)
- [ ] Hard limits live in **code**, not in the prompt (money, deletions, emails sent). *Step 2: the 200 EUR rule in `issue_refund`.*
- [ ] Simple checks on the answer: words it must say or must never say, length, format.
- [ ] Run them on every commit, like any unit test.

## 2 · An LLM judge for meaning
- [ ] Write **golden questions** with the answer you expect (start with 10 to 20 real ones).
- [ ] Score each answer with a bigger model than the one under test. *Step 4:*
  - **Relevance**: does it answer the question?
  - **Groundedness**: is every claim backed by your documents?
  - **Hallucination**: does it contradict known facts?
  - **Accuracy**: does it match the expected answer?
- [ ] Read the judge's **reasons**, not just the scores. Set pass marks on purpose.

## 3 · The agent's journey
- [ ] Record every tool call and every step. *Steps 2 and 3: `tools_used` and the crew's diary.*
- [ ] Assert on the path: the right tools, in the right order, and context passed between agents. *Step 5.*
- [ ] Attack it: "my manager approved it", a fake order number, a system that's down.
- [ ] Turn on tracing (LangSmith or similar), so a failed test shows you where it went wrong.

## 4 · Test the tester
- [ ] Score the same answer a few times. Does the judge's score wobble?
- [ ] Compare the judge with **your own** scores on 10 answers. Do you agree?
- [ ] Count the cost: judge calls × questions × metrics × runs per day.

## Questions to ask your team
1. Which of our AI features could make a decision without any code checking it?
2. Do we have golden questions? Who owns the expected answers?
3. When the model or the prompt changes, which of these checks run automatically?

---
Workshop code: https://github.com/gauravkhuraana/zero-to-evaluated · Gaurav Khurana · #SharingIsCaring
