
# ==========================================================
# SQL AGENT USING PYDANTICAI
# ==========================================================
#
# This module creates an AI agent that can:
#
# 1. Inspect the DuckDB database schema.
# 2. Generate SQL queries from natural language questions.
# 3. Execute SQL queries using registered tools.
# 4. Return structured results using a Pydantic model.
#
# Model: OpenAI GPT-4o-mini
# Database: DuckDB (NYC Yellow Taxi January 2024)
#
# ==========================================================


# ----------------------------------------------------------
# IMPORTS
# ----------------------------------------------------------

# Load environment variables from the .env file.
# This includes OPENAI_API_KEY, required by GPT-4o-mini.
from dotenv import load_dotenv

load_dotenv()


# BaseModel defines the structure of the agent's output.
# Field provides descriptions to help the LLM understand
# what information belongs in each field.
from pydantic import BaseModel, Field

# Import the Agent class from PydanticAI.
from pydantic_ai import Agent

# Import our SQL tools and database setup function.
from sql_tools import SQLTools, setup_database


# ----------------------------------------------------------
# 1. DEFINE THE STRUCTURED OUTPUT MODEL
# ----------------------------------------------------------

class SQLResult(BaseModel):
    """
    Structured output returned by the SQL agent.

    Instead of returning only plain text, the agent
    must return three fields:

    1. sql_query   - the SQL query executed
    2. result_text - the result returned by DuckDB
    3. row_count   - the number of rows returned

    Pydantic validates the structure automatically.
    """

    # Store the SQL query generated and executed by the agent.
    sql_query: str = Field(
        description="The SQL query executed against DuckDB"
    )

    # Store the actual data returned by the database.
    result_text: str = Field(
        description="The SQL query result as text"
    )

    # Store the number of result rows.
    #
    # For an AVG() or COUNT() query without grouping,
    # the database normally returns one aggregated row.
    row_count: int = Field(
        description="Number of rows returned by the SQL query"
    )


# ----------------------------------------------------------
# 2. CREATE THE SQL TOOLS
# ----------------------------------------------------------

# Create an instance of SQLTools.
#
# SQLTools is defined in sql_tools.py and contains:
#
# get_schema()  - describes the trips table
# run_sql()     - executes SQL and returns results
#
sql_tools = SQLTools()


# ----------------------------------------------------------
# 3. CREATE THE PYDANTICAI AGENT
# ----------------------------------------------------------

agent = Agent(

    # Select the OpenAI model used by our agent.
    "openai:gpt-4o-mini",

    # Specify the required Pydantic output model.
    output_type=SQLResult,

    # Register both database methods as agent tools.
    #
    # PydanticAI allows the LLM to request these
    # methods when it needs database information.
    tools=[
        sql_tools.get_schema,
        sql_tools.run_sql,
    ],

    # Define instructions for the SQL agent.
    instructions="""
    You are an SQL assistant working with a DuckDB database.

    The database contains a table named trips with
    NYC Yellow Taxi trip records.

    IMPORTANT:
    Always call get_schema first before generating
    or executing SQL queries.

    Follow these steps:

    1. Call get_schema to inspect available columns.

    2. Identify the columns relevant to the question.

    3. Generate a valid DuckDB SELECT query.

    4. Execute the query using run_sql.

    5. Read the actual result returned by DuckDB.

    6. Return a structured SQLResult object.

    The SQLResult object must contain:

    - sql_query:
      The SQL query that was actually executed.

    - result_text:
      The actual result returned by DuckDB.

    - row_count:
      The number of rows returned by the query.

    For questions involving averages, use AVG().

    For questions involving counts, use COUNT(*).

    For questions involving time of day,
    use EXTRACT(HOUR FROM tpep_pickup_datetime).

    Use appropriate GROUP BY and ORDER BY clauses
    when comparing aggregated values.

    Never invent SQL results.
    Only report values returned by the database.
    """
)


# ----------------------------------------------------------
# 4. RUN THE SQL AGENT
# ----------------------------------------------------------

# This block executes only when we run:
#
# uv run python sql_agent.py
#
# When pytest imports the agent, this block does not execute.
#
if __name__ == "__main__":

    # STEP 1: Prepare the DuckDB database.
    #
    # setup_database() downloads the taxi dataset
    # if necessary and creates the trips table.
    setup_database()


    # STEP 2: Define both homework questions.
    #
    # A Python dictionary stores the question name
    # as the key and the question text as the value.
    #
    # This allows us to test multiple questions
    # without duplicating the agent code.
    questions = {

        # QUESTION 2
        "Question 2 - Average Trip Distance": (
            "What's the average trip distance "
            "for rides with 2 passengers?"
        ),

        # QUESTION 5
        "Question 5 - Highest Average Fare": (
            "Which hour of the day has the "
            "highest average fare amount?"
        ),
    }


    # STEP 3: Process the questions one at a time.
    #
    # .items() returns the question name
    # and corresponding question text.
    for question_name, question in questions.items():

        # Print the name of the homework question.
        print("\n" + "=" * 60)
        print(question_name)
        print("=" * 60)

        # Display the natural language question.
        print("\nQuestion:", question)


        # STEP 4: Execute the SQL agent.
        #
        # run_sync() sends the question to GPT-4o-mini.
        #
        # The agent should:
        # - call get_schema()
        # - generate SQL
        # - call run_sql()
        # - return SQLResult
        #
        # Each question starts a new independent run.
        result = agent.run_sync(question)


        # STEP 5: Extract the structured output.
        #
        # result.output is an instance of SQLResult.
        output = result.output


        # STEP 6: Display the generated SQL query.
        print("\nSQL query:")
        print(output.sql_query)


        # STEP 7: Display the actual database result.
        print("\nQuery result:")
        print(output.result_text)


        # STEP 8: Display the returned row count.
        print("\nRows returned:", output.row_count)


    # STEP 9: Print a completion message.
    print("\nAll questions processed.")
