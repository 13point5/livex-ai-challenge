import os
import json
import instructor
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from calcom import CalAPI

load_dotenv()

app = FastAPI()

cal_api_client = CalAPI(api_key=os.environ.get("CALCOM_API_KEY"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
instructor_client = instructor.from_openai(openai_client)


@app.get("/")
def read_root():
    return {"Hello": "World"}


tools = [
    {
        "type": "function",
        "function": {
            "name": "book_meeting",
            "description": "Book or schedule a meeting for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "time": {
                        "type": "string",
                        "description": "The date and time for the meeting, eg: 2024-07-03T16:40:00.332Z . The last 3 digits with the Z are for the timezone. The timezone is America/NewYork so use appropriate timezone. Don't ask for this format from the user, convert the user's query into this format",
                    },
                    "purpose": {
                        "type": "string",
                        "description": "The purpose/reason/title of the meeting",
                    },
                },
                "required": ["time", "purpose"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scheduled_events",
            "description": "Get list of scheduled events/meetings of the user",
            "parameters": {},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_meeting",
            "description": "Cancel a meeting for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "time": {
                        "type": "string",
                        "description": "The date and time for the meeting",
                    },
                },
                "required": ["time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_meeting",
            "description": "Reschedule a meeting for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_time": {
                        "type": "string",
                        "description": "The date and time for the meeting",
                    },
                    "new_time": {
                        "type": "string",
                        "description": "The date and time for the meeting",
                    },
                },
                "required": ["original_time", "new_time"],
            },
        },
    },
]


class MeetingId(BaseModel):
    id: int | None


def get_meeting_id_from_time(timestamp: str):
    bookings = cal_api_client.get_bookings()
    bookings = bookings["bookings"]
    active_bookings = [
        {"id": b["id"], "startTime": b["startTime"]}
        for b in bookings
        if b["status"] != "CANCELLED"
    ]

    print(json.dumps(active_bookings, indent=2))

    response = instructor_client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=MeetingId,
        max_retries=3,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Find the meeting id around this timestamp. If it doesn't exist return None. Timestamp: {timestamp}\n\n"
                    f"{active_bookings}"
                ),
            }
        ],
    )

    return response.id


class ChatRequest(BaseModel):
    query: str
    history: list[Dict[str, Any]]


@app.post("/chat")
def chat(body: ChatRequest):
    query = body.query

    messages = [
        {
            "role": "system",
            "content": "You are a chatbot who helps users to manage their events by interacting with their cal.com account. When listing their meetings only list active ones by default unless they ask for canceled ones as well.",
        }
    ]

    messages += body.history

    messages.append({"role": "user", "content": query})

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    response_message = response.choices[0].message

    tool_calls = response_message.tool_calls

    any_tool_called = False

    if tool_calls:
        for tool_call in tool_calls:
            if tool_call.type != "function":
                continue

            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "book_meeting":
                function_response = cal_api_client.create_booking(
                    start=function_args.get("time"),
                    title=function_args.get("purpose"),
                )
            elif function_name == "get_scheduled_events":
                function_response = cal_api_client.get_bookings()
            elif function_name == "cancel_meeting":
                meeting_id = get_meeting_id_from_time(
                    timestamp=function_args.get("time")
                )
                if meeting_id is None:
                    function_response = "Error: Could not find meeting"
                else:
                    function_response = cal_api_client.cancel_meeting(
                        meeting_id
                    )
            elif function_name == "reschedule_meeting":
                meeting_id = get_meeting_id_from_time(
                    timestamp=function_args.get("original_time")
                )
                if meeting_id is None:
                    function_response = "Error: Could not find meeting"
                else:
                    function_response = cal_api_client.reschedule_meeting(
                        id=meeting_id, new_time=function_args.get("new_time")
                    )
            else:
                continue

            if not any_tool_called:
                messages.append(response_message)
                any_tool_called = True

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response, indent=2),
                }
            )

        if any_tool_called:
            second_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            second_response_message = second_response.choices[0].message

            messages.append(
                {
                    "role": second_response_message.role,
                    "content": second_response_message.content,
                }
            )
    else:
        messages.append(
            {"role": response_message.role, "content": response_message.content}
        )

    return messages[1:]
