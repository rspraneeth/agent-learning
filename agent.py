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

def get_hour_from_time(time_str: str = None, **kwargs) -> int:
    """Extract the hour (as a number) from a time string like '11:05:25'."""
    value = time_str or next(iter(kwargs.values()))
    return int(value.split(":")[0])


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
    {
        "type": "function",
        "function": {
            "name": "get_current_time_date_and_day",
            "description": "Get the current time, date, and day of the week as a string.",
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
            "name": "get_hour_from_time",
            "description": "Extract the hour as an integer from a time string like '11:05:25'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_str": {
                        "type": "string",
                        "description": "A time string in HH:MM:SS format, e.g. '11:05:25'."
                    }
                },
                "required": ["time_str"],
            },
        }
    }
]

# messages = [{"role": "user", "content": "What is the current date and time with day of the week? Add 10 and 20 together. Can you give answer for both questions I asked?"}]
# messages = [{"role": "user", "content": "What is 15 plus the current hour?"}]
# messages = [{"role": "user", "content": "First call get_current_time to get the time. Then look at that result and tell me only the hour as a number. Do not call any other tool yet."}]
messages = [{"role": "user", "content": "You must answer using tools, one at a time. Never put a tool name or code as an argument value — arguments must be actual values like numbers or strings. Step 1: Call get_current_time. Wait for the real result. Step 2: Call get_hour_from_time, passing the exact string that get_current_time returned. Step 3: Call add with a=15 and b=the hour from step 2. Do only one tool call per turn."}]


# map tool names to the actual functions, so we can look them up by name
available_tools = {
    "get_current_time": get_current_time,
    "add": add,
    "get_current_date": get_current_date,
    "get_current_day": get_current_day,
    "get_current_time_date_and_day": get_current_time_date_and_day,
    "get_hour_from_time": get_hour_from_time
}

max_steps = 10
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