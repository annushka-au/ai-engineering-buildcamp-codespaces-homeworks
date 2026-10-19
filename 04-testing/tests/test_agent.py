
# Import pytest for writing automated tests.
import pytest

# Import our existing SQL agent.
from sql_agent import agent

# Import the database setup function.
from sql_tools import con, setup_database

# Import the collect_tools helper function from utils.py.
# It extracts the tool calls from the agent's message history,
# allowing us to verify which tools were called and in what order.
from utils import collect_tools


# --------------------------------------------------
# TEST: COUNT TRIPS WITH MORE THAN 5 PASSENGERS
# --------------------------------------------------

# The agent runs asynchronously, so we tell pytest
# to handle this test using asyncio.
@pytest.mark.asyncio
async def test_passenger_count():

    # STEP 1: Make sure the database is ready.
    setup_database()

    # STEP 2: Define the question for the agent.
    question = "How many trips had more than 5 passengers?"

    # STEP 3: Run the AI agent.
    #
    # 'await' waits for the asynchronous agent
    # to complete its execution.
    result = await agent.run(question)

    # STEP 4: Extract the structured SQLResult object.
    output = result.output

    # STEP 5: Display results for debugging.
    print("Generated SQL:", output.sql_query)
    print("Query result:", output.result_text)

    # STEP 6: Verify that the generated SQL is not empty.
    assert isinstance(output.sql_query, str)
    assert len(output.sql_query.strip()) > 0

    # STEP 7: Verify that the result contains
    # the actual count returned by DuckDB.
    #
    # Replace 12345 with the number from Step 1.
    expected_count = 22413

    assert str(expected_count) in output.result_text



@pytest.mark.asyncio
async def test_tool_order():
    """
    Verify that the SQL agent gets the schema
    before executing a SQL query.
    """

    # Make sure the database is ready.
    setup_database()

    # Ask the SQL agent a question.
    result = await agent.run(
        "What is the most common payment type?"
    )

    # Get the message history for this run.
    messages = result.new_messages()

    # Extract the tool calls in execution order.
    tool_calls = collect_tools(messages)

    # Print the tools for debugging.
    print("Tools called:")
    for tool in tool_calls:
        print(tool.name)

    # Verify that the agent called at least two tools.
    assert len(tool_calls) >= 2

    # The first tool must inspect the schema.
    assert tool_calls[0].name == "get_schema"

    # The second tool should execute SQL.
    assert tool_calls[1].name == "run_sql"


# ==========================================================
# QUESTION 6 - ADDITIONAL AGENT TESTS
# ==========================================================


# ----------------------------------------------------------
# HELPER: VERIFY TOOL CALL ORDER
# ----------------------------------------------------------

def check_tool_order(result):
    """
    Check that the agent:
    1. Calls get_schema first.
    2. Calls run_sql after inspecting the schema.
    """

    # Extract tool calls from the agent's messages.
    tool_calls = collect_tools(result.new_messages())

    # Get the names of the tools.
    tool_names = [call.name for call in tool_calls]

    print("Tools called:", tool_names)

    # There must be at least two tool calls.
    assert len(tool_names) >= 2

    # First call must inspect the schema.
    assert tool_names[0] == "get_schema"

    # SQL execution must happen after schema inspection.
    assert "run_sql" in tool_names[1:]


# ----------------------------------------------------------
# TEST 1: AVERAGE TIP FOR CREDIT CARD PAYMENTS
# ----------------------------------------------------------

@pytest.mark.asyncio
async def test_average_credit_card_tip():

    setup_database()

    # Calculate the expected result directly in DuckDB.
    expected = con.execute("""
        SELECT ROUND(AVG(tip_amount), 2)
        FROM trips
        WHERE payment_type = 1
    """).fetchone()[0]

    # Ask the AI agent.
    result = await agent.run(
        "What is the average tip amount "
        "for credit card payments?"
    )

    output = result.output

    print("SQL:", output.sql_query)
    print("Expected tip:", expected)
    print("Agent result:", output.result_text)

    # Verify the SQL uses the required columns.
    sql = output.sql_query.lower()

    assert "tip_amount" in sql
    assert "payment_type" in sql

    # Check the agent called tools in the right order.
    check_tool_order(result)

    # Convert the agent's returned text into a number.
    actual = float(output.result_text.strip())

    # Compare numerical values instead of text.
    #
    # expected = 4.17
    # actual   = 4.169670627490153
    #
    # pytest.approx allows small numerical differences.
    assert actual == pytest.approx(float(expected), abs=0.005)


# ----------------------------------------------------------
# TEST 2: PICKUP LOCATION WITH THE MOST TRIPS
# ----------------------------------------------------------

@pytest.mark.asyncio
async def test_busiest_pickup_location():

    setup_database()

    # Find the pickup location with the most trips.
    expected = con.execute("""
        SELECT PULocationID, COUNT(*) AS trip_count
        FROM trips
        GROUP BY PULocationID
        ORDER BY trip_count DESC
        LIMIT 1
    """).fetchone()

    expected_location = expected[0]
    expected_count = expected[1]

    # Ask the agent.
    result = await agent.run(
        "Which pickup location (PULocationID) "
        "has the most trips?"
    )

    output = result.output

    print("SQL:", output.sql_query)
    print("Expected location:", expected_location)
    print("Expected trips:", expected_count)
    print("Agent result:", output.result_text)

    # Verify the required column.
    assert "pulocationid" in output.sql_query.lower()

    # Verify tool call order.
    check_tool_order(result)

    # Check the correct pickup location is returned.
    assert str(expected_location) in output.result_text


# ----------------------------------------------------------
# TEST 3: AVERAGE FARE FOR TRIPS LONGER THAN 10 MILES
# ----------------------------------------------------------

@pytest.mark.asyncio
async def test_average_fare_long_trips():

    setup_database()

    # Calculate average fare for trips over 10 miles.
    expected = con.execute("""
        SELECT ROUND(AVG(fare_amount), 2)
        FROM trips
        WHERE trip_distance > 10
    """).fetchone()[0]

    # Ask the SQL agent.
    result = await agent.run(
        "What is the average fare for trips "
        "longer than 10 miles?"
    )

    output = result.output

    print("SQL:", output.sql_query)
    print("Expected fare:", expected)
    print("Agent result:", output.result_text)

    # Verify the necessary columns.
    sql = output.sql_query.lower()

    assert "fare_amount" in sql
    assert "trip_distance" in sql

    # Verify tool call order.
    check_tool_order(result)

    # Check the actual average fare.
    assert f"{float(expected):.2f}" in output.result_text


# ----------------------------------------------------------
# TEST 4: TRIPS WITH ZERO PASSENGERS
# ----------------------------------------------------------

@pytest.mark.asyncio
async def test_zero_passenger_trips():

    setup_database()

    # Calculate the exact count directly in DuckDB.
    expected = con.execute("""
        SELECT COUNT(*)
        FROM trips
        WHERE passenger_count = 0
    """).fetchone()[0]

    # Ask the agent.
    result = await agent.run(
        "How many trips had zero passengers recorded?"
    )

    output = result.output

    print("SQL:", output.sql_query)
    print("Expected count:", expected)
    print("Agent result:", output.result_text)

    # Verify the correct column is used.
    assert "passenger_count" in output.sql_query.lower()

    # Verify tool call order.
    check_tool_order(result)

    # Verify the returned count.
    assert str(expected) in output.result_text


# ----------------------------------------------------------
# TEST 5: BUSIEST DAY OF THE WEEK
# ----------------------------------------------------------

@pytest.mark.asyncio
async def test_busiest_weekday():

    setup_database()

    # Find the weekday with the highest number of trips.
    #
    # DAYOFWEEK returns:
    # Sunday = 0, Monday = 1, ..., Saturday = 6
    expected = con.execute("""
        SELECT
            DAYOFWEEK(tpep_pickup_datetime) AS weekday,
            COUNT(*) AS trip_count
        FROM trips
        GROUP BY weekday
        ORDER BY trip_count DESC
        LIMIT 1
    """).fetchone()

    expected_day = expected[0]
    expected_count = expected[1]

    # Ask the SQL agent.
    result = await agent.run(
        "What is the busiest day of the week "
        "for taxi trips?"
    )

    output = result.output

    print("SQL:", output.sql_query)
    print("Expected weekday number:", expected_day)
    print("Expected trip count:", expected_count)
    print("Agent result:", output.result_text)

    # Verify that the query uses pickup datetime.
    assert "tpep_pickup_datetime" in output.sql_query.lower()

    # Verify tool call order.
    check_tool_order(result)

    # Convert DuckDB weekday numbers to day names.
    day_names = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]

    expected_day_name = day_names[expected_day]

    # Accept either the weekday name or numeric code.
    assert (
        expected_day_name.lower() in output.result_text.lower()
        or str(expected_day) in output.result_text
    )

