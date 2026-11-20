"""
VERSION 2 · The same agent, now with the book                       (Part 1 · Exercise 1)

v2 = v1 + ONE new tool + TWO new rules. Everything else (the loop, the shop's systems, the 200 EUR rule)
is imported from v1_agent.py unchanged. That is the whole point: grounding is a small change with a big effect.

    NEW TOOL   search_policy   asks the librarian (shared/retrieval.py) for the ShopKart policy pages
                               that best match a question. This is RAG: Retrieval-Augmented Generation.
    NEW RULES  answer only from those pages; if the pages don't say it, say you don't know.

        question --> agent asks for search_policy --> librarian --> policy pages --+
                                                                                    +--> grounded answer
        job description + question ------------------------------------------------+

Remember: wrong pages in -> confident wrong answer out.
So when a grounded agent is wrong, first ask "what did the librarian bring?" (the "sources" in every reply).

Nothing to edit in this file. Ask v1 and v2 the same questions and compare.

RUN IT (from the project folder, with .venv active)
    python run.py --version 2 "Do you price-match?"      # v1 guessed. What does v2 say?
    python run.py --version 2 1100                        # clearance sneakers: final sale. Did v1 refund them?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shared"))  # find shared/config.py
sys.path.insert(0, str(Path(__file__).resolve().parent))                  # find v1_agent.py
import planted_bugs  # noqa: E402   (Part 2 only: does nothing unless you plant a bug)
import v1_agent  # noqa: E402
from langsmith import traceable  # noqa: E402   (does nothing unless LANGSMITH_TRACING=true in .env)
from retrieval import retrieve  # noqa: E402   (the librarian: plain keyword search, no AI)


# NEW in v2 · the tool: find the policy pages that match the question
def search_policy(question):
    pages = retrieve(question, top_k=3)
    return planted_bugs.tamper_pages(pages, question)    # Part 2 only: does nothing unless a bug is planted


TOOLS = v1_agent.TOOLS + [
    v1_agent.describe_tool(
        "search_policy",
        "Search ShopKart's official policy pages (returns, refunds, damaged items, shipping, warranty ...). "
        "Use it before answering any question about what ShopKart allows, and before any refund.",
        question={"type": "string", "description": "What to look up, e.g. 'return window for shoes'"}),
]

# NEW in v2 · the grounding rules, added to v1's job description
SYSTEM_PROMPT = v1_agent.SYSTEM_PROMPT + """
Before answering a policy question or deciding a refund, ALWAYS call search_policy.
Answer ONLY from the policy pages it returns. If the pages don't cover it, say you don't have that
information and offer to connect a human colleague. Never invent policies, discounts, fees or compensation."""


@traceable(name="v2 agent")
def run_agent(message, chaos=None):
    """Version 2: the same loop as v1, with the policy book on the menu."""
    return v1_agent.run_loop(message, SYSTEM_PROMPT, TOOLS,
                             look_ups={"get_order": v1_agent.get_order, "search_policy": search_policy},
                             chaos=chaos)


if __name__ == "__main__":
    print("Run it through run.py from the project folder, e.g.:  python run.py --version 2 \"Do you price-match?\"")
