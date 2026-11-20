"""
The API: FastAPI puts all three agent versions behind one door                (Part 1 and Part 2)

Customers (and, in Part 2, our tests) never import the agent. They send JSON to a URL, exactly like
any web API you have tested before:

    POST /chat   {"message": "Refund order 1043.", "version": 2}
             ->  {"reply": "...", "outcome": {...}, "steps": [...], "sources": [...], "context": [...]}

        reply     what the customer sees
        outcome   what actually happened: refund / escalate / no_refund (+ order and amount)
        steps     the flight recorder: every tool call, in order (Part 2 checks the journey with it)
        sources   which policy pages the agent read (v2, v3)
        context   the text of those pages (Part 2's AI judge checks the answer against it)

"version" is optional. Leave it out and you get AGENT_VERSION from .env (default 3, the crew).

Nothing to edit in this file.

RUN IT (from the project folder, with .venv active)
    uvicorn agent.app:app --reload
    then open http://localhost:8000/docs  ->  POST /chat  ->  Try it out
"""

import os
import sys
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))            # find shared/config.py
sys.path.insert(0, str(Path(__file__).resolve().parent))   # find the agent versions
import config  # noqa: E402

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

sys.stdout.reconfigure(errors="replace")   # Windows consoles can't print every character a model uses

DEFAULT_VERSION = int(os.getenv("AGENT_VERSION", "3"))
app = FastAPI(title="ShopKart Agent", description="One agent, three versions. Try POST /chat.")


def agent_for(version: int):
    """Import the agent version on demand, so a problem in one version never stops the others."""
    if version == 1:
        import v1_agent as agent
    elif version == 2:
        import v2_agent as agent
    else:
        import v3_crew as agent
    return agent


class ChatRequest(BaseModel):
    message: str = Field(examples=["Do you price-match?", "Refund order 1043."])
    version: Literal[1, 2, 3] | None = Field(default=None, description="1 = tools only, 2 = + policy (RAG), 3 = crew")
    chaos: str | None = Field(default=None, description="Part 2 only: 'order_system_down' or 'reviewer_says_no'")


@app.post("/chat")
def chat(req: ChatRequest):
    version = req.version or DEFAULT_VERSION
    print(f"\n[v{version}] customer: {req.message[:80]!r}")
    result = agent_for(version).run_agent(req.message, chaos=req.chaos)

    # The crew (v3) keeps its policy reading in the flight recorder: collect it as evidence too.
    if "context" not in result:
        result["context"] = [str(s["content"]) for s in result.get("steps", [])
                             if s.get("type") == "tool_result" and s.get("name") in ("check_policy", "search_policy")]
        result["sources"] = []

    for step in result["steps"]:
        if step.get("type") in ("tool_call", "action", "proposal"):
            print(f"       {step.get('agent', ''):<17} {step['type']:<10} {step.get('name', '')} {step.get('args', '')}")
    print(f"       outcome: {result['outcome']}")
    result["version"] = version
    return result


@app.post("/agent", include_in_schema=False)
def agent_endpoint(req: ChatRequest):
    """Older name for the crew endpoint, kept so earlier scripts still work."""
    req.version = req.version or 3
    return chat(req)


# ---------------------------------------------------------------------------
# Small read-only endpoints: handy for exploring, and for checking the bot is alive
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/docs")


@app.get("/health")
def health():
    return {"status": "ok", "model": config.LLM_MODEL, "default_version": DEFAULT_VERSION}


@app.get("/orders")
def orders():
    import json
    return json.loads((config.DATA_DIR / "orders.json").read_text(encoding="utf-8"))


@app.get("/policies")
def policies():
    return sorted(page.stem for page in (config.DATA_DIR / "policies").glob("*.md"))


@app.get("/policies/{name}")
def policy(name: str):
    page = config.DATA_DIR / "policies" / f"{Path(name).stem}.md"
    if not page.exists():
        raise HTTPException(status_code=404, detail=f"No policy page called {name}")
    return {"name": page.name, "text": page.read_text(encoding="utf-8")}
