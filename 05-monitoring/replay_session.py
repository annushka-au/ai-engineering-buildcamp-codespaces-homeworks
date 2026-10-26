
import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from logfire.query_client import LogfireQueryClient
from trace_replay import TraceData, trace_to_run_result

load_dotenv()

TRACE_ID = "01a17839f92365b581e32db7e4b09b94"

MODEL_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def calculate_cost(model_name, input_tokens, output_tokens):
    prices = MODEL_PRICES[model_name.lower()]
    return (
        input_tokens * prices["input"]
        + output_tokens * prices["output"]
    ) / 1_000_000


sql = f"""
SELECT
    start_timestamp,
    attributes->'pydantic_ai.all_messages' AS all_messages,
    attributes->>'gen_ai.aggregated_usage.input_tokens' AS input_tokens,
    attributes->>'gen_ai.aggregated_usage.output_tokens' AS output_tokens
FROM records
WHERE trace_id = '{TRACE_ID}'
  AND (
    span_name = 'agent run'
    OR span_name LIKE 'invoke_agent %'
  )
ORDER BY start_timestamp ASC
"""

with LogfireQueryClient(
    read_token=os.environ["LOGFIRE_READ_TOKEN"]
) as client:
    data = client.query_json_rows(
        sql=sql,
        min_timestamp=datetime.now(timezone.utc) - timedelta(days=365),
    )

total_input = 0
total_output = 0
replayed_runs = 0

for row in data["rows"]:
    input_tokens = int(row.get("input_tokens") or 0)
    output_tokens = int(row.get("output_tokens") or 0)

    total_input += input_tokens
    total_output += output_tokens

    messages = row.get("all_messages")
    if messages:
        if isinstance(messages, str):
            messages = json.loads(messages)

        trace = TraceData(
            all_messages=messages,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        replayed = trace_to_run_result(trace)
        replayed_runs += 1
        print(f"Replayed run {replayed_runs}: {replayed.output}")

cost = calculate_cost(
    "gpt-4o-mini",
    total_input,
    total_output,
)

print(f"\nAgent runs found: {len(data['rows'])}")
print(f"Successfully replayed: {replayed_runs}")
print(f"Total input tokens: {total_input}")
print(f"Total output tokens: {total_output}")
print(f"Total cost: ${cost:.6f}")
