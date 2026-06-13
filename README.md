# Agent From Scratch — a learning build

A hand-written **agent loop** using a local LLM (`llama3.2` via Ollama), built
to understand what an agent actually *is* underneath frameworks like LangGraph
or tools like Cursor — and, just as importantly, **where agents fail and why**.

No framework. The loop is written by hand so every step is visible. The local
model is small *on purpose*: its failures are loud and frequent, which makes the
real failure modes of agents easy to see and reason about.

## What an agent is (the one-line version)

An LLM on its own makes a single decision: given a question and a list of tools,
it replies with either an answer or a request to call a tool. **That's the
engine.** The *agent* is the **loop around it** that you build: run the requested
tool, feed the result back, and ask again — repeating until the model produces a
final answer. The model decides *what* to do each step; your loop is what turns a
sequence of decisions into goal-directed behavior.

> Engine vs. car: Ollama is the engine that fires once per turn. The agent is the
> car — the loop, the tool execution, the feedback, the stop condition. You build
> the car.

## The loop (think → act → observe → repeat)

1. Send the conversation history + tool descriptions to the model.
2. If the reply is a final answer → print it, stop.
3. If the reply is a tool call → run the tool, append the result to the history,
   loop again.
4. A hard step cap prevents runaway loops.

The growing conversation history *is* the agent's memory — each pass sees
everything from prior passes.

## Tools in this build

Simple local Python functions: `get_current_time`, `get_current_date`,
`get_current_day`, a composite `get_current_time_date_and_day`, and `add`.
A tool is just a function plus a JSON schema (name, description, parameters)
that the model reads to decide what to call.

## The reliability findings (the real point of this project)

The same code, run repeatedly on the same question, produced **wildly different
outcomes** — because LLMs are non-deterministic (they sample, so identical input
can give different output). Mapping where it's reliable and where it isn't:

| Task type | Reliability |
|-----------|-------------|
| Single tool call ("what time is it?") | Works reliably |
| Independent multi-tool ("date+time AND add 10+20") | Mostly works; sometimes drops part of the answer in synthesis |
| **Dependent chaining** ("15 plus the current hour") | **Fails** — see below |

### Why dependent chaining breaks

Dependent chaining = one tool's *output* must become the next tool's *input*.
The model would fetch the time (`11:05:25`) fine, but then could not reliably
**extract `11` and pass it to `add`** — it kept passing the literal string
`'get_current_time'` (or even shell syntax `$(get_current_time)`) as the
argument. It understands *what* it needs but not the mechanics of "call A, read
A's result, then call B with that value." This is a planning-depth limit of the
small model.

### The scariest failure mode: confident, clean-looking wrong answers

Several runs fetched the correct data and then **fabricated a different value in
the final answer** — e.g. fetched `2026-06-13`, then reported `2023-12-01`; or
fetched the real time but reported a made-up hour. These answers *look* perfectly
correct — sensible numbers, confident phrasing — and are only catchable by
checking against ground truth. A failure that looks like success is more
dangerous than one that looks like a failure.

### Prompting vs. capability

Improving the prompt ("fetch the current hour *from* the current time") raised
the success rate noticeably — the model attempted the right plan more often. But
in the "successful" runs, the tool call still errored and the model **recovered
by doing the arithmetic in its own head**, not by making the chain work. So:

- **Prompting** can coax the model toward the right behavior and right answer
  (on easy enough numbers) — but it papers over the capability gap rather than
  closing it. If the math were too big to do mentally, the wins would vanish.
- **A better model** is what actually fixes the *mechanism* (reliably parsing a
  value out of one tool's output and passing it to the next).

## Defensive scaffolding (mandatory for any agent, any model)

Failures hit during these experiments forced real defenses, all of which a
production agent keeps regardless of model quality:

- **Iteration cap** — an unbounded `while True` ran away, re-calling a tool
  dozens of times. Replaced with a fixed step limit.
- **`try/except` around tool calls** — a crashing tool (bad arg types, missing
  tool) no longer kills the script; the error is fed back to the model, which can
  sometimes recover.
- **Input coercion** — the model often sends arguments as strings (`"10"`), so
  tools must coerce (`int(...)`) rather than assume clean types.
- **Schema/executable sync** — the tool the model is *told about* (the schema)
  and the tool the code can *run* (the dict) must match, or you get a KeyError
  when the model requests a phantom tool.

## Setup & run

Requires Python 3.10+, [Ollama](https://ollama.com/) running, and `llama3.2`
pulled (`ollama pull llama3.2`).

```bash
pip install ollama
python agent.py
```

Edit the `messages` question at the top of the loop and run repeatedly to watch
the (non-deterministic) behavior.

## Biggest takeaways

- The **loop is the agent**; the model only supplies per-step decisions.
- LLMs are **non-deterministic** — same input, different output. You don't debug
  this away; you build defenses that survive it.
- **Fetching the right data does not guarantee the model uses it** — it can
  ignore, override, or fabricate over a tool result.
- **Always verify agent output against ground truth.** Plausible ≠ correct. The
  clean-looking wrong answer is the one that ships.
- A better model raises the reliability floor a lot, but never to 100% — so the
  defensive scaffolding and output validation are the real, permanent job.

## Next step

Phase 2: connect this loop to an MCP server instead of local functions, making it
a pure MCP client (no file access) — and watch a "lying" tool fool it completely,
since it can only ever see the tool's description and result.
