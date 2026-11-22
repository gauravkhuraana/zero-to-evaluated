"""
The web API: FastAPI puts our chatbot, agent and crew behind URLs, like any API you have tested.

Run it (from the project folder, with .venv active):
    uvicorn app:app --reload

Then open http://localhost:8000/docs, pick an endpoint, click "Try it out".
"""
from fastapi import FastAPI
from pydantic import BaseModel

from step1_chatbot.chatbot import SYSTEM_PROMPT, ask_chatbot
from step2_agent.agent import ask_agent
from step3_crew.crew import ask_crew

app = FastAPI(title="ShopKart AI")


# What every request looks like: {"question": "..."}
class Question(BaseModel):
    question: str


# Step 1 · the chatbot (one question, one answer: no memory between requests)
@app.post("/chat")
def chat(body: Question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": body.question},
    ]
    answer = ask_chatbot(messages)
    return {"answer": answer}


# Step 2 · the agent (tools + RAG)
@app.post("/agent")
def agent(body: Question):
    return ask_agent(body.question)


# Step 3 · the crew (multi-agent)
@app.post("/crew")
def crew(body: Question):
    return ask_crew(body.question)
