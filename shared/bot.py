"""
shared/bot.py · How every Part 2 test talks to the agent: over HTTP, like any API test. You never edit this file.

    import bot
    result = bot.ask("Do you price-match?", version=2)
    result["reply"], result["outcome"], result["steps"], result["context"]

Which version? The one you pass in. Otherwise AGENT_VERSION (from .env, or set by pytest --agent-version), else 3.
Where is the bot? SHOPKART_URL in .env (your own laptop by default, or the hosted bot).
"""
import os

import httpx

import config


def default_version() -> int:
    return int(os.getenv("AGENT_VERSION", "3"))


def ask(message: str, version: int | None = None, chaos: str | None = None) -> dict:
    """Send one customer message to POST /chat and return the JSON answer. A fresh agent run every time."""
    response = httpx.post(
        f"{config.SHOPKART_URL}/chat",
        json={"message": message, "version": version or default_version(), "chaos": chaos},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()


def tools_in_order(result: dict) -> list[str]:
    """The flight recorder, flattened: the tools the agent asked for, in order (look-ups + the action)."""
    return [step["name"] for step in result["steps"] if step["type"] in ("tool_call", "proposal")]
