
# ==========================================================
# API COST TRACKING FOR PYDANTICAI
# ==========================================================

# Import the Agent class so we can track its runs.
from pydantic_ai import Agent

# Store total token usage for each model.
usage_totals = {}

# Course pricing in USD per 1 million tokens.
MODEL_PRICES = {
    "openai:gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    }
}

# Keep the original Agent.run method.
original_run = Agent.run

# Prevent installing the tracker more than once.
is_patched = False


def patch_agent():
    """
    Wrap Agent.run to automatically record token usage
    after every successful agent execution.
    """

    global is_patched

    if is_patched:
        return

    async def tracked_run(self, *args, **kwargs):

        # Execute the original PydanticAI agent.
        result = await original_run(self, *args, **kwargs)

        # Get token usage from the completed agent run.
        # In PydanticAI 2.57, usage is a property,
        # so we do not add parentheses.
        usage = result.usage

        # Identify the model used by this agent.
        model = self.model
        model_name = (
            f"{model.system}:{model.model_name}"
        )

        # Initialise totals for this model.
        if model_name not in usage_totals:
            usage_totals[model_name] = {
                "input": 0,
                "output": 0,
                "requests": 0,
            }

        # Accumulate token usage across test runs.
        usage_totals[model_name]["input"] += (
            usage.input_tokens or 0
        )

        usage_totals[model_name]["output"] += (
            usage.output_tokens or 0
        )

        usage_totals[model_name]["requests"] += (
            usage.requests or 0
        )

        return result

    # Replace Agent.run with our tracking wrapper.
    Agent.run = tracked_run

    is_patched = True


def display_total_usage():
    """
    Calculate and display the approximate API cost.
    """

    print("\n" + "=" * 55)
    print("PYDANTICAI API COST REPORT")
    print("=" * 55)

    total_cost = 0.0

    for model, usage in usage_totals.items():

        prices = MODEL_PRICES.get(model)

        print(f"\nModel: {model}")
        print(f"Input tokens: {usage['input']}")
        print(f"Output tokens: {usage['output']}")
        print(f"Model requests: {usage['requests']}")

        if prices is None:
            print("No pricing configured for this model.")
            continue

        # Calculate input token cost.
        input_cost = (
            usage["input"] / 1_000_000
        ) * prices["input"]

        # Calculate output token cost.
        output_cost = (
            usage["output"] / 1_000_000
        ) * prices["output"]

        # Add both costs.
        model_cost = input_cost + output_cost

        total_cost += model_cost

        print(f"Model cost: ${model_cost:.6f}")

    print("\n" + "-" * 55)
    print(f"TOTAL ESTIMATED COST: ${total_cost:.6f} USD")
    print("-" * 55)
