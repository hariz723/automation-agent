"""Finalizer node: compiles and presents the final solution to the user."""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AutomationState


def finalizer_node(state: AutomationState, llm) -> Dict[str, Any]:
    """Synthesize results from all executed steps into a complete, high-quality final deliverable."""
    task = state.get("task", "")
    plan = state.get("plan", [])
    step_history = state.get("step_history", [])

    history_records = []
    for h in step_history:
        history_records.append(
            f"### Step {h.get('step_id')}: {h.get('title')}\n"
            f"{h.get('result')}\n"
        )
    full_history = "\n".join(history_records)

    system_prompt = """You are a Principal AI Automation Deliverer.
Your goal is to synthesize the results of all completed steps into a clear, comprehensive, and polished final response for the user.

Ensure you:
1. Directly answer and deliver what the user requested in their initial prompt.
2. Highlight any files created or modified, code written, data analyzed, or actions automated.
3. Provide code snippets, file paths, or key insights cleanly using markdown.
4. Keep the tone professional, concise, and helpful.
"""

    prompt = f"""Original User Prompt:
{task}

Execution Summary & Step Results:
{full_history}

Please write the final deliverable to present to the user.
"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ])
        final_text = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        final_text = f"Automation completed successfully.\n\nSummary of actions:\n{full_history}"

    return {
        "final_output": final_text,
    }
