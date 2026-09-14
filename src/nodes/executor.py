"""Executor node: executes the current step in the plan using tools."""

from typing import Dict, Any, List
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    BaseMessage,
)
from src.state import AutomationState, SubTask
from src.tools.registry import ALL_TOOLS, TOOL_MAP


def executor_node(state: AutomationState, llm) -> Dict[str, Any]:
    """Execute the active step from the plan using tool-calling agent loop."""
    plan: List[SubTask] = list(state.get("plan", []))
    current_index: int = state.get("current_step_index", 0)
    task: str = state.get("task", "")
    step_history = list(state.get("step_history", []))
    context = dict(state.get("context", {}))
    feedback = state.get("evaluation_feedback")
    retry_count = state.get("retry_count", 0)

    if current_index >= len(plan):
        return {"last_step_result": "All steps executed."}

    current_step = plan[current_index]
    current_step["status"] = "in_progress"

    # Format history summary of previously completed steps
    history_summary = []
    for h in step_history:
        history_summary.append(
            f"Step {h.get('step_id')}: {h.get('title')}\n"
            f"Result: {h.get('result')}\n"
        )
    history_str = "\n---\n".join(history_summary) if history_summary else "No prior steps yet."

    system_instruction = f"""You are an autonomous AI Execution Agent capable of completing tasks using tools.
You are currently executing Step {current_step.get('id')}: '{current_step.get('title')}'.

Overall User Goal:
{task}

Previous Completed Steps:
{history_str}

Current Step Instructions:
{current_step.get('description')}

Expected Output Criteria:
{current_step.get('expected_output')}

Guidelines:
1. Use the provided tools (file operations, Python REPL, web search, shell) to fulfill this step.
2. If code needs to be executed or tested, use 'execute_python' or 'execute_shell'.
3. If files need to be created or read, use 'write_file' or 'read_file'.
4. If web information is needed, use 'web_search' or 'fetch_webpage'.
5. Once you have performed the necessary actions and verified the result, provide a clear, concise summary of what was accomplished and the concrete output.
"""

    user_msg_content = f"Execute step {current_step.get('id')}: {current_step.get('title')}."
    if feedback and retry_count > 0:
        user_msg_content += f"\n\nNote: Previous attempt needed correction. Evaluator feedback:\n{feedback}"

    messages: List[BaseMessage] = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_msg_content),
    ]

    # Tool calling agent loop
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    max_iterations = 8
    iteration = 0
    final_step_text = ""

    while iteration < max_iterations:
        iteration += 1
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        # Check if the model made tool calls
        if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
            for tool_call in ai_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call.get("id", "call_default")

                if tool_name in TOOL_MAP:
                    try:
                        tool_output = TOOL_MAP[tool_name].invoke(tool_args)
                    except Exception as err:
                        tool_output = f"Tool execution error: {str(err)}"
                else:
                    tool_output = f"Error: Tool '{tool_name}' not found."

                # Append tool result to messages
                messages.append(
                    ToolMessage(
                        tool_call_id=tool_id,
                        content=str(tool_output),
                        name=tool_name,
                    )
                )
        else:
            # Final text response from the model
            final_step_text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)
            break

    if not final_step_text:
        final_step_text = "Step completed with tool executions."

    # Update step record
    current_step["result"] = final_step_text
    current_step["status"] = "completed"

    step_history.append({
        "step_id": current_step.get("id"),
        "title": current_step.get("title"),
        "result": final_step_text,
    })

    return {
        "plan": plan,
        "last_step_result": final_step_text,
        "step_history": step_history,
        "context": context,
    }
