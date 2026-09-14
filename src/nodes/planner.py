"""Planner node: breaks down the user prompt into structured subtasks."""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.state import AutomationState, SubTask
from src.tools.registry import get_tool_descriptions


class StepSchema(BaseModel):
    """Schema for an individual subtask."""

    id: int = Field(description="Sequential step number starting from 1")
    title: str = Field(description="Short title summarizing the subtask")
    description: str = Field(
        description="Detailed instructions on what needs to be performed, what tools/files to use"
    )
    expected_output: str = Field(
        description="Clear criteria for when this step is successfully completed"
    )


class PlanSchema(BaseModel):
    """Schema for the overall execution plan."""

    steps: list[StepSchema] = Field(
        description="1 to 5 sequential steps required to complete the user's prompt"
    )


def planner_node(state: AutomationState, llm) -> dict:
    """Analyze the user's prompt and generate a step-by-step execution plan."""
    task = state.get("task", "")
    tool_desc = get_tool_descriptions()

    system_prompt = f"""You are an expert AI Automation Architect.
Your job is to decompose the user's task into an efficient, logical, step-by-step plan (1 to 5 steps).
Each step must be actionable and accomplish a concrete part of the overall use case.

Available Automation Tools:
{tool_desc}

Guidelines:
1. Keep the plan focused and deterministic (typically 2 to 4 steps).
2. If the task requires data gathering, web research, or scraping, include a research/fetch step.
3. If the task requires computation, data processing, or script execution, use Python REPL or shell.
4. If the task requires generating files, scripts, or reports, specify file creation steps.
5. Provide clear 'expected_output' for each step so the evaluator can verify completion.
"""

    user_prompt = f"User Task / Use Case to automate:\n{task}\n\nFormulate the execution plan."

    plan_steps: list[SubTask] = []

    # Attempt structured output first
    try:
        structured_llm = llm.with_structured_output(PlanSchema)
        response: PlanSchema = structured_llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        for s in response.steps:
            plan_steps.append(
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "expected_output": s.expected_output,
                    "status": "pending",
                    "result": None,
                }
            )
    except Exception:
        # Fallback to direct prompt with JSON instructions
        fallback_prompt = (
            system_prompt
            + "\nRespond ONLY with a valid JSON object matching this schema:\n"
            + '{"steps": [{"id": 1, "title": "...", "description": "...", "expected_output": "..."}]}'
        )
        resp = llm.invoke(
            [
                SystemMessage(content=fallback_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        content = resp.content if hasattr(resp, "content") else str(resp)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            for s in data.get("steps", []):
                plan_steps.append(
                    {
                        "id": int(s.get("id", len(plan_steps) + 1)),
                        "title": s.get("title", f"Step {len(plan_steps) + 1}"),
                        "description": s.get("description", ""),
                        "expected_output": s.get("expected_output", ""),
                        "status": "pending",
                        "result": None,
                    }
                )

    # Ultimate fallback if empty
    if not plan_steps:
        plan_steps = [
            {
                "id": 1,
                "title": "Execute Goal",
                "description": f"Directly execute and complete the requested task: {task}",
                "expected_output": "The user's prompt is completely fulfilled.",
                "status": "pending",
                "result": None,
            }
        ]

    return {
        "plan": plan_steps,
        "current_step_index": 0,
        "step_history": [],
        "context": {},
        "retry_count": 0,
        "last_step_result": None,
        "evaluation_status": "continue",
        "evaluation_feedback": None,
        "final_output": None,
        "error": None,
    }
