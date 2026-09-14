"""Replanner node: adapts remaining subtasks dynamically upon failure or changes."""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from src.state import AutomationState, SubTask
from src.tools.registry import get_tool_descriptions


class StepSchema(BaseModel):
    id: int = Field(description="Sequential step number")
    title: str = Field(description="Short title")
    description: str = Field(description="Instructions")
    expected_output: str = Field(description="Success criteria")


class ReplannedSteps(BaseModel):
    remaining_steps: List[StepSchema] = Field(description="Updated sequence of remaining steps to complete the task")


def replanner_node(state: AutomationState, llm) -> Dict[str, Any]:
    """Dynamically adjust the remaining steps in the plan to overcome blockers."""
    task = state.get("task", "")
    plan = list(state.get("plan", []))
    current_index = state.get("current_step_index", 0)
    feedback = state.get("evaluation_feedback", "Previous step encountered an issue.")
    tool_desc = get_tool_descriptions()

    completed_steps = plan[:current_index]

    prompt = f"""Goal: {task}

Feedback/Issue encountered on Step {current_index + 1}:
{feedback}

Available Tools:
{tool_desc}

Previously completed steps:
{completed_steps}

Please formulate an updated sequence of remaining steps (1 to 3 steps) to circumvent the blocker and achieve the original goal.
"""

    updated_remaining: List[SubTask] = []
    try:
        structured_llm = llm.with_structured_output(ReplannedSteps)
        res: ReplannedSteps = structured_llm.invoke([
            SystemMessage(content="You are an adaptive planning agent that revises task steps when blockers occur."),
            HumanMessage(content=prompt),
        ])
        start_id = len(completed_steps) + 1
        for i, s in enumerate(res.remaining_steps):
            updated_remaining.append({
                "id": start_id + i,
                "title": s.title,
                "description": s.description,
                "expected_output": s.expected_output,
                "status": "pending",
                "result": None,
            })
    except Exception:
        # Fallback: keep existing step or simplify
        updated_remaining = [{
            "id": len(completed_steps) + 1,
            "title": "Alternative Execution",
            "description": f"Use alternative approaches or tools to accomplish: {task}",
            "expected_output": "Goal accomplished despite prior errors.",
            "status": "pending",
            "result": None,
        }]

    new_plan = completed_steps + updated_remaining

    return {
        "plan": new_plan,
        "retry_count": 0,
        "evaluation_status": "continue",
        "evaluation_feedback": None,
    }
