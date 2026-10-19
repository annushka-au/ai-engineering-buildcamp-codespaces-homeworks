
# Pydantic models define the judge's structured output.
from pydantic import BaseModel, Field

# PydanticAI runs the judge using an LLM.
from pydantic_ai import Agent

# Import our existing helper that collects tool calls.
from utils import collect_tools


# --------------------------------------------------
# 1. EVALUATION OF ONE CRITERION
# --------------------------------------------------

class JudgeCriterion(BaseModel):
    """Evaluation of one requirement."""

    criterion_description: str = Field(
        description="The requirement being evaluated."
    )

    passed: bool = Field(
        description="True if the requirement was satisfied."
    )

    judgement: str = Field(
        description="Explanation supported by evidence."
    )


# --------------------------------------------------
# 2. COMPLETE JUDGE FEEDBACK
# --------------------------------------------------

class JudgeFeedback(BaseModel):
    """Evaluation report for all criteria."""

    criteria: list[JudgeCriterion] = Field(
        description="Evaluation of each requirement."
    )

    feedback: str = Field(
        description="Overall assessment of the agent."
    )


# --------------------------------------------------
# 3. JUDGE INSTRUCTIONS
# --------------------------------------------------

judge_instructions = """
You are an expert judge evaluating an AI SQL agent.

Evaluate every criterion independently.

Use the SQL query, actual result, tool calls,
and reference answer as evidence.

Do not assume an answer is correct without evidence.

For each criterion, return:
- criterion_description
- passed
- judgement

Evaluate all criteria provided by the user.
""".strip()


# --------------------------------------------------
# 4. CREATE THE JUDGE
# --------------------------------------------------

def create_judge_agent():
    """Create a GPT-4o-mini evaluation agent."""

    return Agent(
        name="judge",
        model="openai:gpt-4o-mini",
        instructions=judge_instructions,
        output_type=JudgeFeedback,
    )


# --------------------------------------------------
# 5. EVALUATE THE SQL AGENT
# --------------------------------------------------

async def evaluate_agent_performance(
    result, criteria, reference_answer
):
    """Evaluate the agent against natural-language criteria."""

    # Extract the real tool calls from the message history.
    tool_calls = collect_tools(result.new_messages())

    # Convert the structured SQLResult into JSON text.
    output = result.output.model_dump_json()

    # Construct a prompt using the course's pattern.
    prompt = f"""
Evaluate the agent's performance.

<CRITERIA>
{chr(10).join(criteria)}
</CRITERIA>

<AGENT_OUTPUT>
{output}
</AGENT_OUTPUT>

<TOOL_CALLS>
{chr(10).join(str(tc) for tc in tool_calls)}
</TOOL_CALLS>

<REFERENCE_ANSWER>
{reference_answer}
</REFERENCE_ANSWER>
"""

    # Create and execute the judge agent.
    judge_agent = create_judge_agent()
    judge_result = await judge_agent.run(prompt)

    # Return structured feedback.
    return judge_result.output


# --------------------------------------------------
# 6. ASSERT ALL CRITERIA
# --------------------------------------------------

async def assert_criteria(result, criteria, reference_answer):
    """Fail the test if any criterion is not satisfied."""

    feedback = await evaluate_agent_performance(
        result, criteria, reference_answer
    )

    print("\nJudge feedback:")
    print(feedback.feedback)

    # Check that the judge evaluated every requirement.
    assert len(feedback.criteria) == len(criteria)

    # Check each individual evaluation.
    for criterion in feedback.criteria:
        print(
            f"{criterion.criterion_description}: "
            f"{criterion.passed} — {criterion.judgement}"
        )

        assert criterion.passed, (
            f"{criterion.criterion_description}: "
            f"{criterion.judgement}"
        )
