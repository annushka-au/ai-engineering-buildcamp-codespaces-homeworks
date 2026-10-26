
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from logfire.query_client import LogfireQueryClient

load_dotenv()

sql = """
SELECT
    trace_id,
    span_name,
    start_timestamp
FROM records
WHERE span_name = 'trivia_session'
ORDER BY start_timestamp DESC
LIMIT 10
"""

min_timestamp = datetime.now(timezone.utc) - timedelta(days=2)

with LogfireQueryClient(
    read_token=os.environ["LOGFIRE_READ_TOKEN"]
) as client:
    result = client.query_json_rows(
        sql=sql,
        min_timestamp=min_timestamp,
    )

    for row in result["rows"]:
        print(row)
