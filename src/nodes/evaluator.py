"""Evaluator node: validates step completion and directs graph flow."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.config import Config
from src.state import AutomationState


class EvaluationSchema(BaseModel):
    """Schema for evaluating step completion."""

    is_successful: bool = Field(
        description="True if the step output satisfies the expected criteria, False otherwise"
    )
    critique: str = Field(description="Detailed critique explaining what succeeded or what failed")
    recommendation: str = Field(
        description="One of: 'continue' (proceed to next step), 'retry' (try again), or 'replan' (alter remaining plan)"
    )


def evaluator_node(state: AutomationState, llm) -> dict[str, Any]:
    """Evaluate whether the executed step meets the criteria and decide next router state."""
    plan = list(state.get("plan", []))
    current_index = state.get("current_step_index", 0)
    last_result = state.get("last_step_result", "")
    retry_count = state.get("retry_count", 0)
    max_retries = Config.MAX_STEP_RETRIES

    if current_index >= len(plan):
        return {
            "evaluation_status": "finish",
            "evaluation_feedback": None,
        }

    current_step = plan[current_index]

    system_prompt = """You are a Quality & Verification Evaluator for an automated AI workflow.
Your role is to assess whether the output of a specific execution step met its stated requirements.

Be pragmatic and objective:
- If the step executed tools and produced the requested code, file, analysis, or answer, mark it successful.
- Only mark it as unsuccessful if there are unhandled errors, missing deliverables, or completely incorrect results.
"""

    eval_prompt = f"""Task Goal: {state.get("task")}

Step {current_step.get("id")}: {current_step.get("title")}
Description: {current_step.get("description")}
Expected Output: {current_step.get("expected_output")}

Actual Result Produced:
{last_result}

Evaluate if the step is successful and determine the next action ('continue', 'retry', or 'replan').
"""

    is_successful = True
    critique = "Step completed as expected."

    try:
        structured_llm = llm.with_structured_output(EvaluationSchema)
        eval_res: EvaluationSchema = structured_llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=eval_prompt),
            ]
        )
        is_successful = eval_res.is_successful
        critique = eval_res.critique
        eval_res.recommendation.lower().strip()
    except Exception:
        # Fallback to simple regex/heuristic evaluation
        if "error" in last_result.lower() and "exception" in last_result.lower():
            is_successful = False
            critique = "Detected unhandled errors in output."
        else:
            is_successful = True
            critique = "Step produced output."

    is_last_step = (current_index + 1) >= len(plan)

    if is_successful:
        if is_last_step:
            return {
                "evaluation_status": "finish",
                "evaluation_feedback": critique,
                "retry_count": 0,
            }
        else:
            return {
                "evaluation_status": "continue",
                "current_step_index": current_index + 1,
                "evaluation_feedback": critique,
                "retry_count": 0,
            }
    else:
        # Step failed or incomplete
        if retry_count < max_retries:
            return {
                "evaluation_status": "retry",
                "retry_count": retry_count + 1,
                "evaluation_feedback": critique,
            }
        else:
            # Exhausted retries -> replan or advance if critical
            return {
                "evaluation_status": "replan",
                "evaluation_feedback": f"Failed after {max_retries} attempts: {critique}",
            }
