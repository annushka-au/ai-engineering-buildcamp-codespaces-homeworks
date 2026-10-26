
from pydantic_ai import Agent
from dotenv import load_dotenv
import logfire
import questionary

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

# Import TriviaTools from the provided homework code.
# Replace trivia_tools with the actual module name.
from trivia_tools import TriviaTools

instructions = """You are a trivia quizmaster. When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. When the player answers, explain why the correct answer is correct - add interesting context and facts
5. After all questions, give the final score
"""

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
    message_history = []

    while True:
        result = agent.run_sync(
            prompt,
            message_history=message_history
        )
        print(result.output)
        message_history = result.all_messages()

        prompt = input("You (write 'stop' to stop): ")
        if not prompt or prompt.lower().strip() == 'stop':
            break


def ask_feedback():
    result = questionary.select(
        "How was the trivia session?",
        choices=["👍 Good", "👎 Bad", "Skip"],
    ).ask()

    if result is None or result == "Skip":
        return None

    return 1 if "Good" in result else -1


if __name__ == "__main__":
    with logfire.span("trivia_session"):
        run("Let's play 5 easy questions from Science & Nature")

        feedback = ask_feedback()

        if feedback is not None:
            logfire.info(
                "trivia_feedback",
                feedback_score=feedback,
                feedback_type="positive" if feedback == 1 else "negative",
            )

