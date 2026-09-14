"""Runner module providing rich terminal streaming and execution of the LangGraph workflow."""

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.graph import build_automation_graph
from src.state import AutomationState

console = Console()


def print_plan_table(plan: list):
    """Print the execution plan in a formatted Rich table."""
    table = Table(title="📋 Automation Plan", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Title", style="bold white", width=25)
    table.add_column("Description", style="white")
    table.add_column("Expected Output", style="green")

    for step in plan:
        table.add_row(
            str(step.get("id", "-")),
            step.get("title", ""),
            step.get("description", ""),
            step.get("expected_output", ""),
        )
    console.print(table)
    console.print()


def run_automation(
    prompt: str,
    llm=None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Execute an automation task end-to-end through the LangGraph workflow.

    Args:
        prompt: The user prompt or use-case instruction to automate.
        llm: Optional custom BaseChatModel instance (defaults to configured LLM).
        verbose: If True, prints formatted step progress to the console.

    Returns:
        The final state dict of the completed workflow.
    """
    if verbose:
        console.print(
            Panel(
                f"[bold green]User Prompt / Usecase:[/bold green]\n{prompt}",
                title="🤖 LangGraph AI Automation Agent",
                border_style="cyan",
            )
        )

    # Compile the graph
    app = build_automation_graph(llm=llm)

    # Initial state
    initial_state: AutomationState = {
        "task": prompt,
        "plan": [],
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

    final_state: dict[str, Any] = {}

    # Stream graph execution events
    for event in app.stream(initial_state):
        for node_name, state_update in event.items():
            if not verbose:
                continue

            if node_name == "planner":
                plan = state_update.get("plan", [])
                console.print(
                    f"[bold yellow]🎯 Planner:[/bold yellow] Generated {len(plan)} subtasks."
                )
                print_plan_table(plan)

            elif node_name == "executor":
                history = state_update.get("step_history", [])
                last = history[-1] if history else None
                if last:
                    console.print(
                        Panel(
                            f"[bold]Step {last.get('step_id')}: {last.get('title')}[/bold]\n\n"
                            f"{last.get('result', '')[:400]}..."
                            if len(last.get("result", "")) > 400
                            else f"[bold]Step {last.get('step_id')}: {last.get('title')}[/bold]\n\n{last.get('result', '')}",
                            title="⚙️ Execution Step Completed",
                            border_style="blue",
                        )
                    )

            elif node_name == "evaluator":
                status = state_update.get("evaluation_status")
                feedback = state_update.get("evaluation_feedback")
                retry_count = state_update.get("retry_count", 0)

                color = "green" if status in ("continue", "finish") else "yellow"
                console.print(
                    f"[{color}]🔍 Evaluator Decision:[/{color}] Status=[bold]{status}[/bold] | "
                    f"Critique: {feedback} "
                    f"{f'(Retry #{retry_count})' if retry_count > 0 else ''}"
                )
                console.print()

            elif node_name == "replanner":
                console.print(
                    "[bold magenta]🔄 Replanner:[/bold magenta] Plan dynamically adjusted to overcome obstacle."
                )
                new_plan = state_update.get("plan", [])
                print_plan_table(new_plan)

            elif node_name == "finalizer":
                output = state_update.get("final_output", "")
                console.print(
                    Panel(
                        Markdown(output),
                        title="🎉 Automation Complete - Final Deliverable",
                        border_style="green",
                    )
                )

            final_state.update(state_update)

    return final_state
