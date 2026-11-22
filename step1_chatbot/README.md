# Step 1 · A ChatGPT-style chatbot

**The idea:** an LLM only does one thing. You send it messages and it sends back the next one.
The **system prompt** is its job description. **Memory** is just us sending the whole conversation again each time.

## Run it
```bash
python step1_chatbot/chatbot.py
```
Ask a few questions, then type `bye`.

Then put it behind a web API, the way real apps use it:
```bash
uvicorn app:app --reload
```
Open http://localhost:8000/docs, then **POST /chat**, then **Try it out**. Stop the API with Ctrl+C.

## Try these (15 minutes)
1. **Change the job description.** In `chatbot.py`, change `SYSTEM_PROMPT` to make the bot answer like a pirate, or only in one word. Run it again.
2. **Change the temperature.** Set `TEMPERATURE = 0`, ask the same question 3 times, then try `1`. What changes?
3. **Test the memory.** Say "My name is Sam", then ask "What's my name?". Then ask it something about ShopKart's real policy, like "Do you price-match?"

## What to notice
- The same question gives **different words** each time. Keep that in mind for step 4.
- It answers confidently about ShopKart's policy **without ever having read it**. That's a hallucination, and step 2 fixes it.
