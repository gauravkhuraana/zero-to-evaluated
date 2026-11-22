"""
STEP 3 · From one agent to a TEAM of agents (multi-agent) with LangGraph

In step 2, ONE agent did everything: looked things up, decided, and paid out.
Now we split the job, like a bank: the person who decides is not the person who checks.

    Researcher  ->  Decider  ->  Checker  ->  Executor
                       ^            |
                       +-- REJECT --+     (the Decider gets one more try)

    Researcher  an LLM finds the order number, then looks up the order and the policy (step 2's tools)
    Decider     an LLM decides: REFUND, NO REFUND or HUMAN, and writes the message to the customer
    Checker     a second LLM checks that decision against the policy: APPROVE or REJECT
    Executor    plain code, no LLM: carries out the approved decision (the 200 EUR rule still applies)

LangGraph is the small library that connects these steps: who goes next, and what they all share.
What they share is a "case file" (a Python dictionary) that every agent reads and adds to.

Run it (from the project folder, with .venv active):
    python step3_crew/crew.py
"""
import json
import os
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from langsmith.wrappers import wrap_openai
from openai import OpenAI

# 1. Settings and the LLM connection (the same as steps 1 and 2)
load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
)
client = wrap_openai(client)   # lets LangSmith record every call (only if LANGSMITH_TRACING=true in .env)
MODEL = os.getenv("LLM_MODEL")

# 2. Reuse the tools from step 2. (The first line tells Python where the step 2 folder is.)
sys.path.append(str(Path(__file__).parent.parent))
from step2_agent.agent import get_order, issue_refund, search_policy  # noqa: E402


# 3. The CASE FILE: everything the agents share. Each agent reads it and fills in its part.
class CaseFile(TypedDict):
    question: str      # what the customer wrote
    order_id: str      # filled in by the Researcher
    order: dict        # filled in by the Researcher
    policy: list       # filled in by the Researcher
    decision: str      # filled in by the Decider
    feedback: str      # filled in by the Checker ("" means approved)
    rounds: int        # how many times the Decider has decided
    action: str        # filled in by the Executor: refund / no refund / human
    answer: str        # what the customer finally sees
    steps: list        # a diary of who did what (the step 5 tests read it)


def ask_llm(instructions, text):
    """One simple LLM call: a job description + a text. Returns the reply."""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip()


# 4. Agent 1 · the RESEARCHER: finds the facts
def researcher(case):
    order_id = ask_llm(
        "Find the order number in the customer's message. Reply with ONLY the number, nothing else.",
        case["question"],
    )
    order = get_order(order_id)

    # Search the policy with the question AND the item name (e.g. "Clearance sneakers", "Laptop")
    item = order.get("item", "")
    policy = search_policy(case["question"] + " " + item)

    case["steps"].append("researcher: looked up order " + order_id + " and " + str(len(policy)) + " policy pages")
    return {"order_id": order_id, "order": order, "policy": policy, "steps": case["steps"]}


# 5. Agent 2 · the DECIDER: decides, using only the facts the Researcher found
DECIDER_INSTRUCTIONS = """You are the Decider at ShopKart. Use ONLY the order and the policy pages.
Your first line must be exactly one of: REFUND, NO REFUND, HUMAN.
Then write a short, friendly message to the customer (max 2 sentences)."""


def decider(case):
    text = "Customer: " + case["question"]
    text = text + "\n\nOrder: " + json.dumps(case["order"])
    text = text + "\n\nPolicy pages:\n" + "\n\n".join(case["policy"])
    if case["feedback"] != "":
        text = text + "\n\nThe Checker rejected your last decision: " + case["feedback"]

    decision = ask_llm(DECIDER_INSTRUCTIONS, text)

    first_line = decision.splitlines()[0]
    case["steps"].append("decider: " + first_line)
    return {"decision": decision, "rounds": case["rounds"] + 1, "steps": case["steps"]}


# 6. Agent 3 · the CHECKER: a second pair of eyes on the decision
CHECKER_INSTRUCTIONS = """You are the Checker at ShopKart. Check the Decider's decision against the order
and the policy pages. Reply APPROVE if it follows the policy. Otherwise reply REJECT and the reason."""


def checker(case):
    text = "Order: " + json.dumps(case["order"])
    text = text + "\n\nPolicy pages:\n" + "\n\n".join(case["policy"])
    text = text + "\n\nDecider's decision:\n" + case["decision"]

    verdict = ask_llm(CHECKER_INSTRUCTIONS, text)

    if verdict.upper().startswith("APPROVE"):
        feedback = ""
    else:
        feedback = verdict

    case["steps"].append("checker: " + verdict.splitlines()[0])
    return {"feedback": feedback, "steps": case["steps"]}


# 7. The ROUTE after the Checker: approved -> Executor. Rejected -> Decider (once more), then Executor.
def after_checker(case):
    if case["feedback"] == "":
        return "executor"
    if case["rounds"] >= 2:
        return "executor"
    return "decider"


# 8. The EXECUTOR: plain code, no LLM. Only this step can move money.
def executor(case):
    decision_lines = case["decision"].splitlines()
    first_line = decision_lines[0].strip().upper()
    message = " ".join(decision_lines[1:]).strip()

    if case["feedback"] != "":
        # The Checker still disagreed after the second try: let a human decide
        action = "human"
        answer = "I've passed your case to a human colleague. You'll hear from us within 2 days."
    elif first_line == "REFUND":
        # The amount comes from the ORDER, not from the LLM
        result = issue_refund(case["order_id"], case["order"]["price_paid"])
        if result.startswith("NOT DONE"):
            action = "human"
            answer = "This refund needs a human colleague's approval. You'll hear from us within 2 days."
        else:
            action = "refund"
            answer = message
    elif first_line == "NO REFUND":
        action = "no refund"
        answer = message
    else:
        action = "human"
        answer = message

    case["steps"].append("executor: " + action)
    return {"action": action, "answer": answer, "steps": case["steps"]}


# 9. Connect the team with LangGraph: who goes after whom
graph = StateGraph(CaseFile)

graph.add_node("researcher", researcher)
graph.add_node("decider", decider)
graph.add_node("checker", checker)
graph.add_node("executor", executor)

graph.set_entry_point("researcher")
graph.add_edge("researcher", "decider")
graph.add_edge("decider", "checker")
graph.add_conditional_edges("checker", after_checker)   # after_checker picks the next step
graph.add_edge("executor", END)

crew = graph.compile()


def ask_crew(question):
    """Run the whole team on one customer message. Returns the finished case file."""
    empty_case = {
        "question": question,
        "order_id": "",
        "order": {},
        "policy": [],
        "decision": "",
        "feedback": "",
        "rounds": 0,
        "action": "",
        "answer": "",
        "steps": [],
    }
    return crew.invoke(empty_case)


# 10. Talk to the team (only when you start THIS file)
if __name__ == "__main__":
    print("ShopKart crew. Type 'bye' to stop. Try: 'I want to return the laptop from order 2001.'")

    while True:
        question = input("\nYou: ")
        if question == "bye":
            break

        case = ask_crew(question)
        for step in case["steps"]:
            print("   ", step)
        print("Crew:", case["answer"])
