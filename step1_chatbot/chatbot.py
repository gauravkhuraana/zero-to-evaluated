"""
STEP 1 · A ChatGPT-style chatbot

An LLM only ever does one thing: you send it messages, it sends back the next message.
"Memory" is just us sending the WHOLE conversation again, every time.

Run it (from the project folder, with .venv active):
    python step1_chatbot/chatbot.py
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

# 1. Read your settings (your key and the model name) from the .env file
load_dotenv()

# 2. Connect to the LLM.
#    Groq speaks the same "language" as OpenAI, so we can use the OpenAI library.
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
)
MODEL = os.getenv("LLM_MODEL")

# 3. The system prompt is the chatbot's job description. Change it and see what happens!
SYSTEM_PROMPT = "You are ShopKart's friendly support assistant. Answer in at most 3 sentences."

# 4. Temperature: 0 = predictable, 1 = creative. Try both!
TEMPERATURE = 0.7


def ask_chatbot(messages):
    """Send the whole conversation to the LLM and return its reply (just the text)."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    answer = response.choices[0].message.content
    return answer


# 5. The chat loop.
#    The "if" line means: only run this part when you start THIS file.
#    (Other files can still use ask_chatbot without starting a chat.)
if __name__ == "__main__":

    # The conversation starts with the job description
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    print("ShopKart chatbot. Type 'bye' to stop.")

    while True:
        # Read the customer's question
        question = input("\nYou: ")
        if question == "bye":
            break

        # Add it to the conversation, ask the LLM, print the reply
        messages.append({"role": "user", "content": question})
        answer = ask_chatbot(messages)
        print("Bot:", answer)

        # Remember the reply too, so the next question has the full history
        messages.append({"role": "assistant", "content": answer})
