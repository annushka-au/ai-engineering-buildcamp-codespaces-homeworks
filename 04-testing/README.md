# Module 04 — Testing and Evaluation of AI Agents

This project demonstrates how to build and test a **PydanticAI SQL agent** that answers natural-language questions about the NYC Yellow Taxi January 2024 dataset.

The agent uses **GPT-4o-mini** to generate SQL queries and **DuckDB** to execute them against approximately 2.96 million taxi trip records.

### What We Implemented

- **SQL Agent:** Converts natural-language questions into SQL queries and returns results.
- **Database Tools:** Provides `get_schema()` and `run_sql()` for interacting with DuckDB.
- **Automated Testing:** Uses pytest to validate answers against SQL reference queries.
- **Tool-Call Verification:** Checks that the agent retrieves the database schema before executing SQL.
- **LLM-as-a-Judge:** Evaluates agent responses against natural-language criteria and expected results.
- **API Cost Tracking:** Records token usage and estimates OpenAI API costs across the test suite.

### Running the Tests

From the `04-testing` directory:

```bash
uv run pytest -v -s
```

### Results

The project includes eight test scenarios: seven SQL agent tests and one LLM judge test.

The recorded estimated API cost for the complete test run was **$0.003076 USD**.

### Technologies

Python, PydanticAI, GPT-4o-mini, DuckDB, pytest, pytest-asyncio, and uv.