
# Import dataclass to represent a tool call.
from dataclasses import dataclass

# Import types for tool arguments.
from typing import Any


# Store information about one tool call.
@dataclass
class ToolCall:
    # Name of the tool, e.g. get_schema or run_sql.
    name: str

    # Arguments passed to the tool.
    args: Any


def collect_tools(messages):
    """
    Extract all real tool calls from the
    agent's message history.

    Ignore the internal final_result tool.
    """

    # Create an empty list for the tool calls.
    tool_calls = []

    # Iterate through the agent's messages.
    for message in messages:

        # Each message contains one or more parts.
        for part in message.parts:

            # Ignore parts that are not tool calls.
            if part.part_kind != "tool-call":
                continue

            # Ignore PydanticAI's internal
            # structured output tool.
            if part.tool_name == "final_result":
                continue

            # Save the tool name and its arguments.
            tool_calls.append(
                ToolCall(part.tool_name, part.args)
            )

    # Return the collected tool calls in order.
    return tool_calls
