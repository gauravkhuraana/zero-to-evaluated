"""
STEP 4a · Why assertEquals fails on AI

Classic testing: same input -> same output, so we compare with ==.
An LLM writes a NEW answer every time. Different words, often the same meaning.

This test asks the chatbot the same question twice and compares the answers with ==.
It is SUPPOSED to fail. Read the two answers in the red output: are they really different?

Run it (from the project folder, with .venv active):
    pytest step4_judge/test_assert_equals.py
"""
from step1_chatbot.chatbot import SYSTEM_PROMPT, ask_chatbot

QUESTION = "How many days do I have to return an item?"


def ask_once():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": QUESTION},
    ]
    return ask_chatbot(messages)


def test_same_question_same_answer():
    first_answer = ask_once()
    second_answer = ask_once()

    print("First answer: ", first_answer)
    print("Second answer:", second_answer)

    # The classic check. Expect this to FAIL: that's the lesson.
    assert first_answer == second_answer
