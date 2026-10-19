
# ==========================================================
# PYTEST COST TRACKING CONFIGURATION
# ==========================================================

# Import dotenv to load the OpenAI API key.
from dotenv import load_dotenv

# Import our cost tracking functions.
from patch_agent import patch_agent, display_total_usage


def pytest_configure(config):
    """
    Called when pytest starts.

    Load the environment and enable API tracking
    before any tests execute.
    """

    # Load OPENAI_API_KEY from the .env file.
    load_dotenv()

    # Activate PydanticAI cost tracking.
    patch_agent()


def pytest_sessionfinish(session, exitstatus):
    """
    Called when pytest finishes its tests.

    Display the combined token usage and cost.
    """

    display_total_usage()
