# Benchmarking an SQL Agent Against Direct Queries

**Context:** As an extension of the Module 04 testing work, I benchmarked the project's PydanticAI SQL agent (GPT-4o-mini + DuckDB) against running the equivalent SQL directly — to measure the real cost of letting an LLM decide and generate the query itself versus hand-writing it.

**Database:** a single DuckDB table, `trips`, loaded from the NYC Yellow Taxi January 2024 Parquet dataset — **2,964,624 records** connected and queried for every run below (confirmed by the `Loaded 2964624 rows` line printed when the benchmark script opens the database).

**Method:** A script (`benchmark.py`) ran each query 30 times directly against DuckDB and 30 times through the full agent pipeline (understand the question → call `get_schema()` → generate SQL → call `run_sql()` → produce an answer), recording latency, correctness against a known reference value, and API cost (via token-usage tracking).

## Query 1: Count of zero-passenger trips

**Question sent to the LLM agent:** *"How many trips had zero passengers recorded?"*

**Equivalent direct SQL:**
```sql
SELECT COUNT(*) FROM trips WHERE passenger_count = 0
```
Reference answer: **31,465**

| Metric | Direct SQL | AI Agent |
|---|---|---|
| Median latency | 0.0007s | 4.30s |
| P95 latency | 0.0011s | 5.69s |
| Min / Max | 0.0006s / 0.0017s | 3.79s / 6.71s |
| Accuracy (30 runs) | 100% | 100% |
| API cost (total / per call) | $0 | $0.010204 / $0.000340 |

## Query 2: Busiest pickup location

**Question sent to the LLM agent:** *"Which pickup location (PULocationID) has the most trips?"*

**Equivalent direct SQL:**
```sql
SELECT PULocationID, COUNT(*) AS trip_count
FROM trips
GROUP BY PULocationID
ORDER BY trip_count DESC
LIMIT 1
```
Reference answer: **PULocationID 132**

| Metric | Direct SQL | AI Agent |
|---|---|---|
| Median latency | 0.0017s | 4.65s |
| P95 latency | 0.0028s | 6.66s |
| Min / Max | 0.0012s / 0.0034s | 3.88s / 6.84s |
| Accuracy (30 runs) | 100% | 100% |
| API cost (total / per call) | $0 | $0.010993 / $0.000366 |

## Takeaways

- **Reliability held up:** across 60 total live agent calls (two different questions × 30 repetitions), the agent got the right answer every single time — no flaky SQL generation, no wrong tool order.
- **The agent is thousands of times slower, not just "a bit slower."** Direct SQL answers in single-digit milliseconds; the agent takes 4–7 seconds, since each run needs about three round trips to GPT-4o-mini. Confirmed by checking `result.usage.requests` after a run — it reported exactly `requests=3` every time (call `get_schema`, call `run_sql` with the generated query, return the final `SQLResult`), with no retries observed in these runs.
- **Query complexity shows up in latency, not accuracy.** The `GROUP BY`/`ORDER BY`/`LIMIT` query (Query 2) was consistently slower and more variable than the simple `WHERE` filter (Query 1) — more output tokens, a longer tail of slow runs — but this didn't cost it any correctness.
- **Cost is genuinely negligible:** roughly a third of a cent per question, ~1 cent for 30 repeated runs of the same question.
- **Bottom line:** if the exact SQL is known ahead of time, there's no reason to route it through an LLM — it's pure overhead. The agent earns its keep specifically when the user doesn't know SQL and needs to ask in plain language; its value is flexibility, not speed.
