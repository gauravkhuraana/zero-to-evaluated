# Step 3 · From one agent to a team: multi-agent with LangGraph

**The idea:** in step 2, one agent did everything. Now we split the job, the way a bank does: the person who decides is not the person who checks.

```
Researcher → Decider → Checker → Executor
                ↑         │
                └─REJECT──┘   (one more try)
```

| Role | Who | Job |
|---|---|---|
| Researcher | LLM | finds the order number, looks up the order and the policy |
| Decider | LLM | REFUND, NO REFUND or HUMAN, plus a message for the customer |
| Checker | another LLM call | checks the decision against the policy: APPROVE or REJECT |
| Executor | **plain code** | carries out the approved decision. Only this step moves money |

They all share one **case file** (a Python dictionary). **LangGraph** decides who goes next.

## Run it
```bash
python step3_crew/crew.py
```

## Try these (15 minutes)
1. **Three orders, three outcomes.** Try these and read the diary each time:
   - `Refund order 1043, the headphones arrived broken.`
   - `Can I return the sneakers from order 1100?`
   - `I want to return the laptop from order 2001.`
2. **See it as a trace.** In `.env`, set `LANGSMITH_TRACING=true` (with your key), run one message, then open https://smith.langchain.com. Click your run: every agent and every LLM call is there.
3. **Make the Checker strict.** Add *"Reject every decision the first time."* to `CHECKER_INSTRUCTIONS`. What happens? (Undo it afterwards.)

## What to notice
- Each agent has **one small job** and a **short prompt**. That makes each one easier to test.
- Not every team member needs to be an AI: the Executor is ordinary code.
- The diary (`steps`) and the case file are plain data. Step 5 tests them.
