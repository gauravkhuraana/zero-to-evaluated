"""
tools/config.py · settings for the setup check (check_setup.py). The workshop programs read .env themselves.

WHAT IT DOES
    Reads your settings from the .env file in the repo root (copy .env.example to .env first)
    and hands out a ready-made "client" that talks to the model.

The workshop programs (step1-step5) do NOT use this file: each one reads .env itself, so you can read it top to bottom.
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Where things live
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent          # the repo root (the folder with .env in it)
DATA_DIR = ROOT / "data"                               # data/: policy pages + orders
load_dotenv(ROOT / ".env")                             # read .env (silently does nothing if it's missing)
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")   # Part 2: DeepEval sends no usage data
os.environ.setdefault("DEEPEVAL_RETRY_MAX_ATTEMPTS", "6")    # free judge APIs frequently need >2 attempts
os.environ.setdefault("DEEPEVAL_RETRY_CAP_SECONDS", "10")

# ---------------------------------------------------------------------------
# The model that powers YOUR bot (Part 1 · BUILD)
# Default = Groq's free cloud. Any OpenAI-compatible server works (Ollama, LM Studio, Azure...).
# ---------------------------------------------------------------------------
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")   # where the model lives
LLM_API_KEY = os.getenv("LLM_API_KEY", "")                # your Groq key (Ollama ignores it: use "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")  # which model to use on that server

# ---------------------------------------------------------------------------
# The AI judge that grades the bot (Part 2 · TEST)
# Default = a bigger open model on Groq's free tier (free key: https://console.groq.com/keys)
# ---------------------------------------------------------------------------
JUDGE_BASE_URL = os.getenv("JUDGE_BASE_URL", "https://api.groq.com/openai/v1")
JUDGE_API_KEY = os.getenv("JUDGE_API_KEY", "")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")

# ---------------------------------------------------------------------------
# Where the agent API runs (uvicorn app:app)
# ---------------------------------------------------------------------------
SHOPKART_URL = os.getenv("SHOPKART_URL", "http://localhost:8000").rstrip("/")


def llm_client() -> OpenAI:
    """The universal plug: the same OpenAI SDK talks to Ollama, Groq, Azure... Only base_url changes."""
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        from langsmith.wrappers import wrap_openai
        return wrap_openai(client)
    return client


def clean(text: str | None) -> str:
    """Some models (e.g. Qwen3) 'think out loud' inside <think>...</think> before answering.
    Customers shouldn't see that, so we cut it out. Returns "" if the model only thought."""
    return re.sub(r"<think>.*?(</think>|$)", "", text or "", flags=re.S).strip()


# ---------------------------------------------------------------------------
# Part 2 helpers: the judge, as DeepEval wants it
# ---------------------------------------------------------------------------
def judge_model():
    """The big AI judge used by DeepEval (Part 2)."""
    from deepeval.models import LocalModel
    return LocalModel(model=JUDGE_MODEL, base_url=JUDGE_BASE_URL, api_key=JUDGE_API_KEY)


def local_judge_model():
    """The same small model the agent runs on, acting as a judge."""
    from deepeval.models import LocalModel
    return LocalModel(model=LLM_MODEL, base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
