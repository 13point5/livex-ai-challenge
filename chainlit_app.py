import chainlit as cl
import requests


@cl.on_chat_start
async def main():
    cl.user_session.set("history", [])


@cl.on_message
async def on_message(message: cl.Message):
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={
            "query": message.content,
            "history": cl.user_session.get("history"),
        },
    )

    response = response.json()
    cl.user_session.set("history", response)

    bot_response = response[-1]["content"]
    await cl.Message(bot_response).send()
