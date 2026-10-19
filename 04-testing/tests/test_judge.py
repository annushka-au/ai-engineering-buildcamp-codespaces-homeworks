
# pytest supports automated tests.
import pytest

# Import the SQL agent we want to test.
from sql_agent import agent

# Import DuckDB connection and database setup.
from sql_tools import con, setup_database

# Import our LLM judge assertion function.
from tests.judge import assert_criteria


# --------------------------------------------------
# TEST: HIGHEST AVERAGE FARE BY HOUR
# --------------------------------------------------

@pytest.mark.asyncio
async def test_highest_average_fare():

    # STEP 1: Prepare the database.
    setup_database()

    # STEP 2: Calculate the reference answer directly.
    #
    # EXTRACT(HOUR ...) gets the hour (0-23).
    # AVG(fare_amount) calculates average fares.
    # GROUP BY groups trips by hour.
    # ORDER BY DESC places the highest average first.
    # LIMIT 1 returns only the highest-ranked hour.
    expected_hour, expected_fare = con.execute("""
        SELECT
            EXTRACT(HOUR FROM tpep_pickup_datetime),
            ROUND(AVG(fare_amount), 2)
        FROM trips
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 1
    """).fetchone()

    print("Correct hour:", expected_hour)
    print("Correct average fare:", expected_fare)

    # STEP 3: Ask the agent the homework question.
    result = await agent.run(
        "Which hour of the day has the highest "
        "average fare amount?"
    )

    print("Agent SQL:", result.output.sql_query)
    print("Agent result:", result.output.result_text)

    # STEP 4: Define natural-language evaluation criteria.
    criteria = [
        "The SQL query correctly calculates average "
        "fare_amount grouped by the hour of day.",

        "The result identifies the specific hour "
        "with the highest average fare amount.",

        "The result includes the actual numerical "
        "average fare amount.",
    ]

    # STEP 5: Provide the independent reference values.
    reference_answer = (
        f"Correct hour: {expected_hour}. "
        f"Correct average fare: ${expected_fare:.2f}."
    )

    # STEP 6: Ask the LLM judge to evaluate the response.
    await assert_criteria(
        result,
        criteria,
        reference_answer
    )
