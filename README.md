# From Zero to Evaluated: build and test an AI agent in half a day

Hands-on workshop · Gaurav Khurana · #SharingIsCaring

**If you get stuck anywhere, contact [Gaurav Khurana on LinkedIn](https://www.linkedin.com/in/gauravkhuraana/).**

You'll build an AI assistant for a made-up online shop, **ShopKart**, in three steps, and then test it in two.
Every program is short, reads top to bottom, and has a comment on every part. Everything is free.

| | Step | You build / test | Key idea |
|---|---|---|---|
| **Build** | [1 · Chatbot](step1_chatbot/) | a ChatGPT-style chatbot, also behind a FastAPI web API | messages, system prompt, temperature, memory |
| | [2 · Agent](step2_agent/) | the chatbot + tools + RAG (it reads the shop's policy) | the LLM asks, our code decides |
| | [3 · Multi-agent](step3_crew/) | a team: Researcher → Decider → Checker → Executor (LangGraph) | split the job, check each other, trace it in LangSmith |
| **Break** | [4 · Judge the answers](step4_judge/) | why `assertEquals` fails; an LLM judge scores the answers | relevance, groundedness, hallucination, accuracy |
| | [5 · Test the agents](step5_agent_tests/) | tests for tools, order, context and task completion | test the journey, not just the answer |

Each step takes 30 minutes: 15 minutes of explanation, then 15 minutes trying things yourself (each step's README has a **Try these** list).

## Before the day
Follow **[SETUP.md](SETUP.md)** (20 to 30 minutes). You are ready when this says **OK** on every line:
```bash
python check_setup.py
```

## On the day
Open the project folder in VS Code and a terminal (**Terminal → New Terminal**). Activate `.venv` in every new terminal:
- Windows: `.venv\Scripts\Activate.ps1`
- Mac/Linux: `source .venv/bin/activate`

Then follow the steps in order. Every command runs from the project folder:

```bash
python step1_chatbot/chatbot.py
```
```bash
uvicorn app:app --reload
```
```bash
python step2_agent/agent.py
```
```bash
python step3_crew/crew.py
```
```bash
pytest step4_judge -v
```
```bash
pytest step5_agent_tests -v
```

Prefer pressing ▶ instead of typing? Open **[workshop.ipynb](workshop.ipynb)**: it runs the same steps.

## What's in the project
| | |
|---|---|
| `step1_chatbot/` … `step5_agent_tests/` | the five steps: one program and one README each |
| `app.py` | the web API: `/chat`, `/agent` and `/crew` (open `/docs` to try them) |
| `data/` | ShopKart's 10 policy pages and 10 example orders (all made up) |
| `TAKE_HOME.md` | the evaluation checklist, for your own team |
| `SETUP.md` · `TROUBLESHOOTING.md` | getting ready · when something goes wrong |
| `setup_env.py` · `check_setup.py` · `tools/` | setup and checks (you don't need to read these) |

## Stuck?
1. Find the FAQ number from `check_setup.py` in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
2. Can't install anything? Use GitHub Codespaces (Path B in [SETUP.md](SETUP.md)).
3. Ask your neighbour. Nobody gets left behind.

Built by Gaurav Khurana ([gauravkhurana.com](https://gauravkhurana.com)). ShopKart and its data are made up.
Uses FastAPI, the OpenAI Python library (with Groq), LangGraph, LangSmith, DeepEval and pytest.
