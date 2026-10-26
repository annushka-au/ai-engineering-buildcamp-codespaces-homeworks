 
"""
TRIVIA AGENT — PYTHON USER MANUAL
=================================

PURPOSE
-------
This program creates an interactive trivia quiz using Pydantic AI.

The agent:
1. Fetches trivia categories and questions using external tools.
2. Asks multiple-choice questions.
3. Evaluates the player's answers.
4. Explains correct answers.
5. Tracks the conversation using message history.
6. Collects user feedback after the session.
7. Sends agent traces and feedback events to Logfire.

TECHNOLOGIES
------------
- Pydantic AI: Builds and runs the AI agent.
- OpenAI GPT-4o-mini: Language model used by the agent.
- Logfire: Records agent execution traces and feedback.
- Questionary: Displays an interactive feedback menu.
- python-dotenv: Loads environment variables from .env.

INSTALLATION
------------
Run in the VS Code terminal:

    uv add pydantic-ai logfire python-dotenv questionary

ENVIRONMENT VARIABLES
---------------------
Create a .env file containing:

    OPENAI_API_KEY=your_openai_api_key
    LOGFIRE_TOKEN=your_logfire_write_token

Keep .env private and exclude it from Git.

PROJECT STRUCTURE
-----------------
trivia-agent/
    .env
    .gitignore
    trivia_agent.py
    trivia_tools.py
    pyproject.toml

The trivia_tools.py module must contain the TriviaTools class.

RUN THE PROGRAM
---------------
From the project directory:

    uv run python trivia_agent.py

The program starts a trivia session with five easy questions
from the Science & Nature category.

To stop the conversation, enter:

    stop

After the session, select:

    Good
    Bad
    Skip

LOGFIRE MONITORING
------------------
Open your Logfire project to inspect:
- trivia_session: Parent span for the entire session.
- Agent execution spans: Model interactions and tool calls.
- trivia_feedback: Feedback log recorded within the parent span.

Feedback values:
     1 = positive
    -1 = negative
  None = skipped

IMPORTANT
---------
The Python program does not calculate the trivia score itself.
The AI agent is instructed to track answers and report the score.

The program also relies on the TriviaTools module to supply
categories and questions.
"""


# ============================================================
# 1. IMPORT REQUIRED LIBRARIES
# ============================================================

# Agent provides the framework for creating a Pydantic AI agent.
from pydantic_ai import Agent

# load_dotenv reads environment variables from the .env file.
from dotenv import load_dotenv

# Logfire records execution traces, tool calls and custom events.
import logfire

# Questionary creates interactive terminal menus.
import questionary


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ============================================================

# Load variables such as OPENAI_API_KEY and LOGFIRE_TOKEN.
#
# This avoids placing secret API credentials directly in code.

load_dotenv()


# ============================================================
# 3. CONFIGURE LOGFIRE OBSERVABILITY
# ============================================================

# Configure Logfire using the project's environment settings.
#
# Logfire allows you to inspect:
# - Agent execution
# - Model requests and responses
# - Tool calls
# - Execution duration
# - Custom feedback events

logfire.configure()


# Automatically instrument Pydantic AI.
#
# Instrumentation means that Logfire can record the agent's
# execution without manually creating logs for every model call.

logfire.instrument_pydantic_ai()


# ============================================================
# 4. IMPORT TRIVIA TOOLS
# ============================================================

# TriviaTools is a class supplied by the homework project.
#
# It provides external functions that the agent can use to
# retrieve trivia categories and questions.
#
# Replace trivia_tools with the actual module name if different.

from trivia_tools import TriviaTools


# ============================================================
# 5. DEFINE AGENT INSTRUCTIONS
# ============================================================

# Instructions describe the agent's role and expected behaviour.
#
# They guide how the language model should interact with users,
# when it should call tools, and how it should evaluate answers.
#
# These are instructions for the model, not Python control flow.
# Python does not independently enforce the number of questions.

instructions = """You are a trivia quizmaster. When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. When the player answers, explain why the correct answer is correct - add interesting context and facts
5. After all questions, give the final score
"""


# ============================================================
# 6. CREATE AN INSTANCE OF TRIVIA TOOLS
# ============================================================

# Create an object of the TriviaTools class.
#
# This object exposes the methods that the agent will use.
#
# get_categories:
#     Retrieves the available trivia categories.
#
# get_questions:
#     Retrieves trivia questions using the tool's parameters.

trivia_tools = TriviaTools()


# ============================================================
# 7. CREATE THE PYDANTIC AI AGENT
# ============================================================

# Agent(...) creates an AI agent configured with:
#
# model:
#     openai:gpt-4o-mini
#
# name:
#     agent
#
# tools:
#     Functions the language model can request.
#
# instructions:
#     Rules describing how the agent should conduct the quiz.
#
# The agent may decide when to call the tools based on the
# instructions and the current conversation.

agent = Agent(
    'openai:gpt-4o-mini',

    name='agent',

    tools=[
        trivia_tools.get_categories,
        trivia_tools.get_questions,
    ],

    instructions=instructions,
)


# ============================================================
# 8. RUN THE INTERACTIVE TRIVIA CONVERSATION
# ============================================================

def run(prompt):
    """
    Run an interactive conversation with the Trivia Agent.

    PARAMETERS
    ----------
    prompt : str
        Initial instruction or the user's next message.

    HOW IT WORKS
    ------------
    1. Initialise an empty message history.
    2. Send the prompt to the agent.
    3. Print the agent's response.
    4. Save the updated conversation history.
    5. Ask the user for another input.
    6. Continue until the user enters 'stop' or an empty input.

    WHY MESSAGE HISTORY IS IMPORTANT
    --------------------------------
    Each agent.run_sync() call is a separate agent execution.

    Without message_history, the agent would not automatically
    receive the earlier conversation on the next call.

    Passing message_history allows the agent to remember:
    - Questions already asked
    - Previous user answers
    - Correct and incorrect responses
    - The current score, as represented in the conversation

    RETURNS
    -------
    None
        The function prints responses rather than returning them.
    """

    # Store all previous model requests and responses.
    #
    # The first execution starts with an empty history.

    message_history = []

    # Continue interacting until the user chooses to stop.

    while True:

        # Execute the agent synchronously.
        #
        # run_sync() waits until the agent has produced its
        # response before continuing to the next Python statement.
        #
        # prompt:
        #     Current user message.
        #
        # message_history:
        #     Conversation messages from earlier turns.

        result = agent.run_sync(
            prompt,
            message_history=message_history
        )

        # Display the agent's final output for this turn.
        #
        # result.output typically contains the text generated
        # for the user.

        print(result.output)

        # Update the conversation history.
        #
        # result.all_messages() includes the message history
        # associated with this execution.
        #
        # This is passed to the next run_sync() call so the
        # conversation can continue.

        message_history = result.all_messages()

        # Ask for the player's next answer or instruction.

        prompt = input("You (write 'stop' to stop): ")

        # End the conversation if:
        #
        # 1. The user presses Enter without typing anything.
        # 2. The user enters 'stop'.
        #
        # strip() removes surrounding whitespace.
        # lower() makes the comparison case-insensitive.
        #
        # Therefore STOP, Stop and stop all work.

        if not prompt or prompt.lower().strip() == 'stop':
            break


# ============================================================
# 9. COLLECT USER FEEDBACK
# ============================================================

def ask_feedback():
    """
    Collect thumbs-up or thumbs-down feedback from the player.

    The feedback is collected using an interactive terminal menu.

    AVAILABLE OPTIONS
    -----------------
    Good:
        Positive feedback, returned as integer 1.

    Bad:
        Negative feedback, returned as integer -1.

    Skip:
        No feedback, returned as None.

    The function also returns None if the menu is cancelled.

    RETURN TYPE
    -----------
    int | None

    EXAMPLES
    --------
    Good  ->  1
    Bad   -> -1
    Skip  -> None

    The actual feedback event is recorded separately in the
    main program using logfire.info().
    """

    # Display an interactive menu.
    #
    # questionary.select() allows the user to choose from
    # predefined options rather than entering free text.

    result = questionary.select(
        "How was the trivia session?",
        choices=["👍 Good", "👎 Bad", "Skip"],
    ).ask()

    # If the user cancelled the menu or selected Skip,
    # return None without recording positive/negative feedback.

    if result is None or result == "Skip":
        return None

    # Convert the selected feedback into a numerical score.
    #
    # "Good" -> 1
    # "Bad"  -> -1

    return 1 if "Good" in result else -1


# ============================================================
# 10. MAIN PROGRAM ENTRY POINT
# ============================================================

# __name__ == "__main__" means:
#
# Execute this section only when the file is run directly.
#
# Example:
#     uv run python trivia_agent.py
#
# If this file is imported by another Python module,
# the code inside this block will not run automatically.

if __name__ == "__main__":

    # --------------------------------------------------------
    # 10.1 CREATE THE PARENT LOGFIRE SPAN
    # --------------------------------------------------------

    # A span represents an operation being monitored.
    #
    # trivia_session is the parent span for the entire
    # interactive quiz session.
    #
    # All instrumented agent executions and tool calls occurring
    # within this context can be associated with the parent trace.
    #
    # This makes it easier to inspect one complete session.

    with logfire.span("trivia_session"):

        # ----------------------------------------------------
        # 10.2 START THE QUIZ
        # ----------------------------------------------------

        # The first prompt instructs the agent to play:
        #
        # - Five questions
        # - Easy difficulty
        # - Science & Nature category
        #
        # The instructions guide the AI model, which is responsible
        # for conducting the quiz and reporting the score.

        run("Let's play 5 easy questions from Science & Nature")

        # ----------------------------------------------------
        # 10.3 ASK FOR SESSION FEEDBACK
        # ----------------------------------------------------

        # After run() finishes, display the feedback menu.
        #
        # Feedback is requested inside trivia_session so the
        # feedback event can be associated with the same trace.

        feedback = ask_feedback()

        # ----------------------------------------------------
        # 10.4 RECORD THE FEEDBACK IN LOGFIRE
        # ----------------------------------------------------

        # Only record feedback if the user selected Good or Bad.
        #
        # A skipped or cancelled response produces no feedback log.

        if feedback is not None:

            # logfire.info() creates a structured log event.
            #
            # "trivia_feedback":
            #     Event message used to identify the feedback.
            #
            # feedback_score:
            #     Numeric value, 1 or -1.
            #
            # feedback_type:
            #     Descriptive label, positive or negative.
            #
            # The event is recorded in the active trace context.

            logfire.info(
                "trivia_feedback",
                feedback_score=feedback,
                feedback_type="positive" if feedback == 1 else "negative",
            )


# ============================================================
# 11. HOW TO INSPECT THE RESULT IN LOGFIRE
# ============================================================

# 1. Run the program:
#
#       uv run python trivia_agent.py
#
# 2. Complete the trivia session or enter "stop".
#
# 3. Select Good or Bad when prompted.
#
# 4. Open your Logfire project.
#
# 5. Search for:
#
#       trivia_session
#
# 6. Open a session trace.
#
# 7. Inspect the nested agent and tool spans.
#
# 8. Look for the feedback log event:
#
#       trivia_feedback
#
# IMPORTANT:
# "trivia_feedback" is the event message passed to logfire.info().
# Its span_name in the Logfire records table may instead be the
# actual logging span name, such as "logfire.log".
#
# To find feedback using SQL, searching the message field may
# therefore be more reliable:
#
#       SELECT
#           trace_id,
#           span_name,
#           message,
#           attributes,
#           start_timestamp
#       FROM records
#       WHERE message = 'trivia_feedback'
#       ORDER BY start_timestamp DESC
#       LIMIT 20
#
# Feedback within the same session should have the same trace_id
# as its parent trivia_session span.
#
# ============================================================
# END OF MANUAL
# ============================================================
