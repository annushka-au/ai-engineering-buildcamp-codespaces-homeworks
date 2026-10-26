
"""
TRIVIA AGENT — QUICK GUIDE
--------------------------
Interactive trivia quiz powered by Pydantic AI and GPT-4o-mini.

Features:
- Fetches multiple-choice questions using TriviaTools.
- Evaluates answers and tracks scores through the AI agent.
- Maintains conversation history between questions.
- Records agent activity and user feedback in Logfire.

Setup:
    uv add pydantic-ai logfire python-dotenv questionary

Required .env variables:
    OPENAI_API_KEY=your_api_key
    LOGFIRE_TOKEN=your_logfire_token

Run:
    uv run python trivia_agent.py

Enter 'stop' to finish.
After the quiz, select Good, Bad, or Skip for feedback.

Logfire:
    trivia_session  - parent trace span
    trivia_feedback - feedback log event
"""

from pydantic_ai import Agent
from dotenv import load_dotenv
import logfire
import questionary

from trivia_tools import TriviaTools

# Load credentials and enable agent tracing.
load_dotenv()
logfire.configure()
logfire.instrument_pydantic_ai()

# Instructions define the quizmaster's behaviour.
instructions = """You are a trivia quizmaster. When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. When the player answers, explain why the correct answer is correct - add interesting context and facts
5. After all questions, give the final score
"""

# Register external trivia tools with the AI agent.
trivia_tools = TriviaTools()

agent = Agent(
    'openai:gpt-4o-mini',
    name='agent',
    tools=[
        trivia_tools.get_categories,
        trivia_tools.get_questions,
    ],
    instructions=instructions,
)


def run(prompt):
    """Run the quiz, preserving conversation history between turns."""
    message_history = []

    while True:
        # Execute the agent and print its answer.
        result = agent.run_sync(
            prompt,
            message_history=message_history
        )
        print(result.output)

        # Preserve previous questions and answers.
        message_history = result.all_messages()

        prompt = input("You (write 'stop' to stop): ")
        if not prompt or prompt.lower().strip() == 'stop':
            break


def ask_feedback():
    """Collect feedback: Good=1, Bad=-1, Skip=None."""
    result = questionary.select(
        "How was the trivia session?",
        choices=["👍 Good", "👎 Bad", "Skip"],
    ).ask()

    if result is None or result == "Skip":
        return None

    return 1 if "Good" in result else -1


if __name__ == "__main__":
    # Keep the entire quiz and feedback within one Logfire trace.
    with logfire.span("trivia_session"):
        run("Let's play 5 easy questions from Science & Nature")

        feedback = ask_feedback()

        # Record feedback within the same trace.
        if feedback is not None:
            logfire.info(
                "trivia_feedback",
                feedback_score=feedback,
                feedback_type="positive" if feedback == 1 else "negative",
            )
