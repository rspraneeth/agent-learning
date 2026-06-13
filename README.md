# Agent From Scratch — a learning build

A hand-written **agent loop** using a local LLM (`llama3.2` via Ollama), built
to understand what an agent actually *is* underneath frameworks like LangGraph
or tools like Cursor — and, just as importantly, **where agents fail, why, and
what it actually takes to make a small model reliable.**

No framework. The loop is written by hand so every step is visible. The local
model is small *on purpose*: its failures are loud and frequent, which makes the
real behavior of agents easy to see and reason about.

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
`get_current_day`, a composite `get_current_time_date_and_day`, `add`, and
`get_hour_from_time` (which takes a time string and returns the hour). A tool is
just a function plus a JSON schema (name, description, parameters) the model
reads to decide what to call.

## The reliability findings (the real point of this project)

The same code, run repeatedly on the same question, produced **wildly different
outcomes** — because LLMs are non-deterministic (they sample, so identical input
can give different output). Mapping where it's reliable and where it isn't:

| Task type | Reliability |
|-----------|-------------|
| Single tool call ("what time is it?") | Works reliably |
| Independent multi-tool ("date+time AND add 10+20") | Mostly works; sometimes drops part of the answer in synthesis |
| **Dependent chaining** ("15 plus the current hour") | Failed for a long time — then *solved*. See the journey below. |

### The dependent-chaining journey (the main lesson)

Dependent chaining = one tool's *output* must become the next tool's *input*
("get the time → extract the hour → add 15"). This was the hard case, and the
path to making it work is the most valuable thing in this repo:

1. **Plain question ("What is 15 plus the current hour?")** — failed almost
   every run. The model would pass the literal string `'get_current_time'` (the
   tool *name*) as the argument instead of the value, or fabricate an hour. It
   understood the task but couldn't express it as a sequence of separate calls.

2. **Added a helper tool (`get_hour_from_time`)** — made it *worse*. One more
   hand-off the model couldn't perform; it started trying to cram nested calls
   into a single argument as strings (`'$(get_hour_from_time ...)'`).

3. **Explicit step-by-step prompt** — improved tool *selection* but still failed
   the hand-off (~1 in 9 success).

4. **A prompt that explicitly (a) numbered the steps, (b) said "pass the exact
   value the previous tool returned," (c) said "never put a tool name as an
   argument," and (d) said "one tool call per turn"** — the model finally passed
   real values forward. Chaining worked. The only remaining error was a trivial
   argument-*naming* mismatch (model sent `t=` / `time=` instead of `time_str=`).

5. **Made the tool tolerant of argument names (`**kwargs`)** — the full
   three-step chain then completed reliably (~7 of 9 runs):
   `get_current_time → 11:33:05 → get_hour_from_time → 11 → add(15, 11) → 26`.

### The conclusion (and a correction)

It is tempting to conclude "small models can't do dependent chaining." That
conclusion would be **wrong**. The chaining was never a hard capability ceiling —
it was a **promptability + tool-design** problem. With a sufficiently explicit
prompt and tools tolerant of imprecise arguments, `llama3.2` chained reliably.

> The biggest lesson: **"the model can't do X" and "I haven't yet found the
> prompt + tool design that lets it do X" look identical from the outside.** The
> only way to tell them apart is to keep testing past the point where you've
> concluded it's impossible. Roughly 40 failed runs preceded the working one.

### Other failure modes seen along the way

- **Confident, clean-looking wrong answers.** Several runs fetched correct data
  then fabricated a different value in the final answer (fetched `2026-06-13`,
  reported `2023-12-01`; fetched the real time, reported a made-up hour). These
  look perfectly correct and are only catchable by checking against ground truth.
  **Always verify agent output against ground truth — plausible ≠ correct.**
- **Describes the action instead of taking it.** Some runs ended with
  `FINAL ANSWER: add(a=15, b=11)` — narrating the final tool call instead of
  executing it.
- **Fetching the right data does not guarantee the model uses it** — it can
  ignore, override, or fabricate over a tool result.

## Defensive scaffolding (mandatory for any agent, any model)

Failures during these experiments forced real defenses, all of which a
production agent keeps regardless of model quality:

- **Iteration cap** — an unbounded `while True` ran away, re-calling a tool
  dozens of times. Replaced with a fixed step limit.
- **`try/except` around tool calls** — a crashing tool (bad arg types, missing
  tool) no longer kills the script; the error is fed back to the model, which can
  sometimes recover.
- **Input coercion** — the model often sends arguments as strings (`"10"`), so
  tools coerce (`int(...)`) rather than assume clean types.
- **Tolerant argument handling (`**kwargs`)** — the model invents argument names
  (`t`, `time`, `tt`); a tolerant tool accepts the value regardless of key.
- **Schema/executable sync** — the tool the model is *told about* (the schema)
  and the tool the code can *run* (the dict) must match, or a phantom-tool request
  throws a KeyError.

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
- **"Can't" vs. "haven't found how yet" are indistinguishable from outside** —
  keep testing past your first conclusion. (The chaining "ceiling" wasn't one.)
- Reliability comes from **explicit prompting + tolerant tool design**, not just
  from a bigger model.
- **Always verify output against ground truth.** The clean-looking wrong answer
  is the one that ships.

## Next step

Phase 2: connect this loop to an MCP server instead of local functions, making it
a pure MCP client (no file access) — and watch a "lying" tool fool it completely,
since it can only ever see the tool's description and result.