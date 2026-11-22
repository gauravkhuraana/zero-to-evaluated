"""
STEP 2 · From chatbot to AGENT: tools + RAG

A chatbot can only talk. An agent can also DO things: it can ask our code to run a "tool".

    1. We give the LLM a menu of tools (just names + descriptions).
    2. The LLM answers either with text, OR with "please run tool X with these inputs".
    3. OUR code runs the tool and sends the result back. Repeat until the LLM answers with text.

The model never touches our systems itself. It can only ASK. Our code decides.

RAG (Retrieval-Augmented Generation) is just one of those tools: search_policy finds the
policy pages that match the question, so the LLM answers from OUR rules, not from its imagination.

Run it (from the project folder, with .venv active):
    python step2_agent/agent.py
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
from openai import OpenAI

# 1. Settings and the LLM connection (the same as step 1)
load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
)
client = wrap_openai(client)   # lets LangSmith record every call (only if LANGSMITH_TRACING=true in .env)
MODEL = os.getenv("LLM_MODEL")


# 2. ShopKart's data: the orders, and the folder with the policy pages
DATA_FOLDER = Path(__file__).parent.parent / "data"

with open(DATA_FOLDER / "orders.json", encoding="utf-8") as file:
    ORDERS = json.load(file)


# 3. The TOOLS: plain Python functions. The LLM can ask for them, our code runs them.

def get_order(order_id):
    """Look up one order by its number."""
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": "No order found with number " + order_id}
    return order


# Words that appear in almost every question or page, so they don't help to find the right page
SKIP_WORDS = ["order", "from", "have", "want", "with", "this", "that", "your", "what", "would", "like", "please"]


def word_roots(text):
    """The words in a text, cut to their first 5 letters, so "refund" and "refunds" count as one word."""
    roots = []
    for word in text.lower().split():
        word = word.strip("?.,!:;()'\"")       # drop punctuation around the word
        if len(word) > 3 and word not in SKIP_WORDS:     # also skip short words like "a", "the", "my"
            roots.append(word[:5])
    return roots


def search_policy(question):
    """RAG: find the 3 policy pages that share the most words with the question."""
    question_roots = word_roots(question)
    scored_pages = []

    for page in DATA_FOLDER.glob("policies/*.md"):
        text = page.read_text(encoding="utf-8")
        page_roots = word_roots(text)

        # Score = how many words of the question also appear in this page
        score = 0
        for root in question_roots:
            if root in page_roots:
                score = score + 1

        scored_pages.append((score, text))

    # Highest score first, keep the best 3 pages
    scored_pages.sort(reverse=True)
    best_pages = []
    for score, text in scored_pages[:3]:
        best_pages.append(text)
    return best_pages


def issue_refund(order_id, amount):
    """Pretend to pay money back. The 200 EUR rule lives HERE, in code: the LLM can't talk its way past it."""
    if amount > 200:
        return "NOT DONE: refunds above 200 EUR need a human colleague."
    return "Refund of " + str(amount) + " EUR issued for order " + order_id


# 4. The MENU: what the LLM sees. Only names, descriptions and inputs. Never the code.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Look up an order: item, price paid, status, days since delivery, condition.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "e.g. 1043"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Search ShopKart's policy pages (returns, refunds, shipping, warranty...).",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Refund money for an order. Only when the policy allows it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number", "description": "in EUR"},
                },
                "required": ["order_id", "amount"],
            },
        },
    },
]

# Which Python function belongs to which tool name
TOOL_FUNCTIONS = {
    "get_order": get_order,
    "search_policy": search_policy,
    "issue_refund": issue_refund,
}


# 5. The job description
SYSTEM_PROMPT = """You are ShopKart's support agent. Be friendly and brief (max 3 sentences).
Always use search_policy before answering a question about returns, refunds or other rules.
Answer ONLY from the policy pages. If they don't cover it, say you don't know.
For a refund: look up the order with get_order, check the policy, and only then use issue_refund."""


# 6. The AGENT LOOP: ask the LLM, run the tools it asks for, repeat until it answers in words
def ask_agent(question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tools_used = []      # which tools the agent asked for, in order (the step 5 tests read this)
    policy_pages = []    # what search_policy found (the step 4 judge checks the answer against it)

    for turn in range(5):    # at most 5 rounds, so it can never loop forever
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )
        reply = response.choices[0].message

        # No tool requested: the LLM answered in words, so we are done
        if not reply.tool_calls:
            return {"answer": reply.content, "tools_used": tools_used, "policy_pages": policy_pages}

        # The LLM asked for one or more tools: remember its request in the conversation
        requested = []
        for tool_call in reply.tool_calls:
            requested.append(tool_call.model_dump())
        messages.append({"role": "assistant", "content": "", "tool_calls": requested})

        # Run each requested tool

        for tool_call in reply.tool_calls:
            name = tool_call.function.name
            inputs = json.loads(tool_call.function.arguments)
            print("   [agent] runs tool:", name, inputs)

            function = TOOL_FUNCTIONS[name]
            result = function(**inputs)       # ** passes the inputs by name, e.g. order_id="1043"

            tools_used.append(name)
            if name == "search_policy":
                policy_pages.extend(result)

            # Send the result back to the LLM, linked to its request
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

    return {"answer": "Sorry, I couldn't finish that. A colleague will help you.",
            "tools_used": tools_used, "policy_pages": policy_pages}


# 7. Chat with the agent (only when you start THIS file)
if __name__ == "__main__":
    print("ShopKart agent. Type 'bye' to stop. Try: 'Refund order 1043, it arrived broken.'")

    while True:
        question = input("\nYou: ")
        if question == "bye":
            break

        result = ask_agent(question)
        print("Agent:", result["answer"])
