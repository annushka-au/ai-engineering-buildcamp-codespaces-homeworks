# AI Engineering BuildCamp — Homeworks

Homework solutions for the [AI BuildCamp](https://aishippinglabs.com/courses/ai-buildcamp/) course by AI Shipping Labs — a hands-on program covering RAG, agents, testing, and observability for LLM applications.

## Modules

| Folder | Topic |
|---|---|
| [`01-foundation/`](01-foundation) | RAG basics (PDF → chunks → index → generative answers) and structured output |
| [`03-agentic-flows/`](03-agentic-flows) | Tool-calling agent (PydanticAI + Wikipedia search) |
| [`04-testing/`](04-testing) | Testing and evaluating an AI agent (SQL agent, pytest, LLM-as-a-judge, cost tracking) |
| [`05-monitoring/`](05-monitoring) | Observability (Logfire tracing, a trivia agent, and session replay from recorded traces) |

## Running a module

Each module is a notebook or a small `uv` project. From the repo root:

```bash
uv sync
uv run jupyter lab        # for the notebooks in 01-foundation / 03-agentic-flows
```

`04-testing` has its own `pyproject.toml`/environment — see its own README for setup and test commands.

Each module expects an `.env` file (not committed) with the API keys it needs, e.g.:

```
OPENAI_API_KEY=...
LOGFIRE_READ_TOKEN=...   # 05-monitoring only
```
