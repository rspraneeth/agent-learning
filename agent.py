import ollama
from datetime import datetime

print("--- SCRIPT STARTED --- \n")

def get_current_time():
    """Return the current time as a string."""
    return datetime.now().strftime("%H:%M:%S")

def get_current_date():
    """Return the current date as a string."""
    return datetime.now().strftime("%Y-%m-%d")

def get_current_day():
    """Return the current day of the week as a string."""
    return datetime.now().strftime("%A")

def get_current_time_date_and_day():
    """Return the current time, date, and day of the week as a string."""
    return f"Time: {get_current_time()}, date: {get_current_date()}, and day: {get_current_day()}."

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return int(a) + int(b)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time right now. Takes no arguments.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "Get the current date.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_day",
            "description": "Get the current day of the week.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "get_current_time_date_and_day",
    #         "description": "Get the current time, date, and day of the week as a string.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {},
    #             "required": [],
    #         },
    #     },
    # }
]

# messages = [{"role": "user", "content": "What is the current date and time with day of the week? Add 10 and 20 together. Can you give answer for both questions I asked?"}]
messages = [{"role": "user", "content": "Whats the current time? What is 15 plus the current hour? May be you can fetch current hour from current time?"}]

# map tool names to the actual functions, so we can look them up by name
available_tools = {
    "get_current_time": get_current_time,
    "add": add,
    "get_current_date": get_current_date,
    "get_current_day": get_current_day,
    # "get_current_time_date_and_day": get_current_time_date_and_day,
}

max_steps = 5
for step in range(max_steps):
    response = ollama.chat(model="llama3.2", messages=messages, tools=tools)
    message = response["message"]
    messages.append(message)

    if not message.tool_calls:
        print("\nFINAL ANSWER:", message.content)
        break

    for call in message.tool_calls:
        name = call.function.name
        print(f"\n[model wants to call: {name} with args: {call.function.arguments}]")
        args = call.function.arguments or {}
        try:
            result = available_tools[name](**args)
        except Exception as e:
            result = f"ERROR running {name}: {e}"
        print(f"[tool returned: {result}]\n")
        messages.append({"role": "tool", "name": name, "content": str(result)})
else:
    print("\n[stopped: hit max steps without a final answer]")