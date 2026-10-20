"""
Benchmark: direct DuckDB SQL vs. the full AI-agent pipeline, for one
representative question.

Direct SQL just executes a known query. The AI agent has to understand the
question, call get_schema(), generate SQL, call run_sql(), and interpret the
result - so this measures both how much slower that extra reasoning makes it
(latency) and how reliably it gets the same answer every time (accuracy).

Usage:
    uv run python benchmark.py

Outputs:
    - A comparison table printed to the console (median/P95/min/max latency,
      accuracy, API cost).
    - benchmark_summary.csv - the same summary metrics.
    - benchmark_agent_runs.csv - per-run latency/correctness for every agent call.
"""

import asyncio
import csv
import statistics
import time

from patch_agent import patch_agent, display_total_usage, usage_totals, MODEL_PRICES
from sql_agent import agent
from sql_tools import con, setup_database

QUESTION = "Which pickup location (PULocationID) has the most trips?"
DIRECT_SQL = """
    SELECT PULocationID, COUNT(*) AS trip_count
    FROM trips
    GROUP BY PULocationID
    ORDER BY trip_count DESC
    LIMIT 1
"""

DIRECT_REPETITIONS = 30
AGENT_REPETITIONS = 30
WARMUP_RUNS = 3

SUMMARY_CSV = "benchmark_summary.csv"
DETAIL_CSV = "benchmark_agent_runs.csv"


def run_direct_sql_once():
    start = time.perf_counter()
    result = con.execute(DIRECT_SQL).fetchone()[0]
    elapsed = time.perf_counter() - start
    return elapsed, result


async def run_agent_once(expected):
    start = time.perf_counter()
    result = await agent.run(QUESTION)
    elapsed = time.perf_counter() - start
    correct = str(expected) in result.output.result_text
    return elapsed, correct


def percentile(values, pct):
    values = sorted(values)
    k = (len(values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] * (c - k) + values[c] * (k - f)


def summarize(latencies):
    return {
        "median": statistics.median(latencies),
        "p95": percentile(latencies, 95),
        "min": min(latencies),
        "max": max(latencies),
    }


async def main():
    setup_database()
    patch_agent()

    expected = con.execute(DIRECT_SQL).fetchone()[0]
    print(f"Question: {QUESTION}")
    print(f"Reference answer (direct SQL): {expected}\n")

    # Warm up both paths so first-call overhead (DB file open, first HTTP
    # connection) doesn't skew the measured runs.
    print("Warming up...")
    for _ in range(WARMUP_RUNS):
        run_direct_sql_once()
    await run_agent_once(expected)

    # Discard any usage captured during warm-up so the cost report below
    # reflects only the measured repetitions.
    usage_totals.clear()

    print(f"Running direct SQL x{DIRECT_REPETITIONS}...")
    direct_latencies = [run_direct_sql_once()[0] for _ in range(DIRECT_REPETITIONS)]

    print(f"Running AI agent x{AGENT_REPETITIONS}...")
    agent_latencies = []
    correct_count = 0
    agent_runs = []
    for i in range(AGENT_REPETITIONS):
        elapsed, correct = await run_agent_once(expected)
        agent_latencies.append(elapsed)
        correct_count += int(correct)
        agent_runs.append({"run": i + 1, "latency_s": round(elapsed, 4), "correct": correct})
        print(f"  run {i + 1}/{AGENT_REPETITIONS}: {elapsed:.2f}s, correct={correct}")

    direct_stats = summarize(direct_latencies)
    agent_stats = summarize(agent_latencies)
    accuracy_pct = 100 * correct_count / AGENT_REPETITIONS

    model_name = "openai:gpt-4o-mini"
    usage = usage_totals.get(model_name, {"input": 0, "output": 0, "requests": 0})
    prices = MODEL_PRICES.get(model_name, {})
    total_cost = (
        usage["input"] / 1_000_000 * prices.get("input", 0)
        + usage["output"] / 1_000_000 * prices.get("output", 0)
    )
    cost_per_call = total_cost / AGENT_REPETITIONS if AGENT_REPETITIONS else 0

    print("\n" + "=" * 72)
    print("BENCHMARK RESULTS")
    print("=" * 72)
    print(f"{'Metric':<20}{'Direct SQL':>24}{'AI Agent':>24}")
    print(f"{'Repetitions':<20}{DIRECT_REPETITIONS:>24}{AGENT_REPETITIONS:>24}")
    print(f"{'Median latency (s)':<20}{direct_stats['median']:>24.4f}{agent_stats['median']:>24.4f}")
    print(f"{'P95 latency (s)':<20}{direct_stats['p95']:>24.4f}{agent_stats['p95']:>24.4f}")
    print(f"{'Min latency (s)':<20}{direct_stats['min']:>24.4f}{agent_stats['min']:>24.4f}")
    print(f"{'Max latency (s)':<20}{direct_stats['max']:>24.4f}{agent_stats['max']:>24.4f}")
    print(f"{'Accuracy':<20}{'100.0%':>24}{f'{accuracy_pct:.1f}%':>24}")
    print(f"{'API cost (total)':<20}{'$0.000000':>24}{f'${total_cost:.6f}':>24}")
    print(f"{'API cost (per call)':<20}{'$0.000000':>24}{f'${cost_per_call:.6f}':>24}")

    slowdown = agent_stats["median"] / direct_stats["median"]
    print(f"\nAgent is ~{slowdown:.0f}x slower than direct SQL (median latency).")

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["method", "metric", "value"])
        writer.writerow(["direct_sql", "repetitions", DIRECT_REPETITIONS])
        for metric, value in direct_stats.items():
            writer.writerow(["direct_sql", metric, value])
        writer.writerow(["ai_agent", "repetitions", AGENT_REPETITIONS])
        for metric, value in agent_stats.items():
            writer.writerow(["ai_agent", metric, value])
        writer.writerow(["ai_agent", "accuracy_pct", accuracy_pct])
        writer.writerow(["ai_agent", "total_cost_usd", total_cost])
        writer.writerow(["ai_agent", "cost_per_call_usd", cost_per_call])

    with open(DETAIL_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "latency_s", "correct"])
        writer.writeheader()
        writer.writerows(agent_runs)

    print(f"\nSaved summary to {SUMMARY_CSV} and per-run detail to {DETAIL_CSV}")

    display_total_usage()


if __name__ == "__main__":
    asyncio.run(main())
