# Step 5 · Test the agents: the journey, not just the answer

**The idea:** a right answer can hide a wrong journey, like a refund paid without looking up the order first.
Tool calls and the crew's diary are **plain data**, so ordinary `assert`s can check them.

| Question | How the test checks it |
|---|---|
| Right tools? | `"get_order" in tools_used` · DeepEval `ToolCorrectnessMetric` |
| Right order? | `tools.index("get_order") < tools.index("issue_refund")` |
| Context passed? | the Researcher's order and pages are in the case file the Decider used |
| Task finished? | an LLM judge (`GEval` "Task completion") reads the final answer |
| Safe? | "my manager approved it" must not trigger a refund |

## Run it
```bash
pytest step5_agent_tests/test_agents.py -v
```

## Try these (15 minutes): break it on purpose
1. **Take away a tool.** In `step2_agent/agent.py`, delete (or comment out) the whole `search_policy` block in `TOOLS`. Rerun the tests: which ones catch it?
2. **Remove the safety rule.** In `issue_refund`, change `200` to `2000`. Does a test turn red, or does the policy page still save you? Run it twice.
3. **Weaken a prompt.** Delete the line *"Always use search_policy..."* from `SYSTEM_PROMPT`. Does anything fail? Is that a test gap?

Undo each change afterwards (in VS Code: Ctrl+Z, or right-click the file → **Revert File** if you use Git).

## What to notice
- Most of these tests need **no AI judge**: they're fast, free and repeatable.
- The LLM judge is only used where meaning matters ("was the task finished?").
- When a test fails, the diary tells you **which agent** went wrong.
