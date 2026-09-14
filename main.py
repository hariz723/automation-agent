#!/usr/bin/env python3
"""Main CLI entrypoint for the LangGraph AI Automation Agent."""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.config import Config
from src.graph import build_automation_graph
from src.llm_factory import get_llm
from src.runner import run_automation

console = Console()


def visualize_graph(output_file: str = "graph.png"):
    """Export and print graph visualization."""
    try:
        from unittest.mock import MagicMock

        # Use dummy LLM to build structure
        app = build_automation_graph(llm=MagicMock())
        mermaid_syntax = app.get_graph().draw_mermaid()
        console.print(
            Panel(mermaid_syntax, title="LangGraph Mermaid Workflow", border_style="cyan")
        )

        try:
            png_bytes = app.get_graph().draw_mermaid_png()
            with open(output_file, "wb") as f:
                f.write(png_bytes)
            console.print(f"[bold green]Saved workflow diagram to {output_file}[/bold green]")
        except Exception:
            console.print(
                "[dim](PNG rendering requires pygraphviz or internet access; Mermaid syntax printed above)[/dim]"
            )
    except Exception as e:
        console.print(f"[bold red]Failed to visualize graph: {e}[/bold red]")


def run_lint(fix: bool = False):
    """Run Ruff linter on the codebase."""
    import subprocess

    cmd = ["ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.append(".")

    console.print(f"[bold cyan]Running linter: {' '.join(cmd)}...[/bold cyan]")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            console.print("[bold green]✅ Lint passed: Codebase is clean![/bold green]")
        else:
            console.print("[bold yellow]⚠️ Lint findings:[/bold yellow]")
            if res.stdout:
                console.print(res.stdout)
            if res.stderr:
                console.print(res.stderr)
    except FileNotFoundError:
        console.print("[bold red]Linter error: 'ruff' not found. Install via 'uv sync'.[/bold red]")


def interactive_mode(llm):
    """Run interactive prompt session."""
    console.print(
        Panel(
            "[bold cyan]LangGraph AI Automation Agent Interactive Shell[/bold cyan]\n"
            "Type your prompt / use case below. Type 'exit' or 'quit' to exit.",
            border_style="cyan",
        )
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Enter Prompt[/bold green]")
            if not user_input.strip():
                continue
            if user_input.strip().lower() in ("exit", "quit", "q"):
                console.print("[yellow]Exiting agent. Goodbye![/yellow]")
                break

            run_automation(prompt=user_input, llm=llm, verbose=True)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session interrupted. Exiting.[/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error running automation: {e}[/bold red]")


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous AI Automation Agent powered by LangGraph, Google Gemini, and Hugging Face."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="The prompt or use-case instruction to automate.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run in interactive prompt loop.",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "huggingface"],
        default=None,
        help="Choose LLM provider (gemini or huggingface). Overrides .env setting.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Specific model name (e.g. gemini-2.5-flash, gemini-2.5-pro, Qwen/Qwen2.5-72B-Instruct).",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Output the LangGraph workflow structure as a Mermaid diagram.",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run code linter (Ruff) across the project.",
    )
    parser.add_argument(
        "--lint-fix",
        action="store_true",
        help="Run code linter and automatically fix issues.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode: only output final deliverable.",
    )

    args = parser.parse_args()

    # If --lint or --lint-fix flag is set
    if args.lint or args.lint_fix:
        run_lint(fix=args.lint_fix)
        return

    # If --visualize flag is set
    if args.visualize:
        visualize_graph()
        return

    # Check configuration
    provider = args.provider or Config.LLM_PROVIDER
    if provider == "gemini" and not Config.GEMINI_API_KEY:
        console.print(
            Panel(
                "[bold red]Gemini API Key Missing![/bold red]\n\n"
                "Please configure your Gemini API key by either:\n"
                "  1. Creating a [bold].env[/bold] file with [bold]GEMINI_API_KEY=your_key_here[/bold]\n"
                "  2. Setting the environment variable: [bold]export GEMINI_API_KEY=your_key_here[/bold]\n\n"
                "You can get a free Gemini API key at: [bold cyan]https://aistudio.google.com/[/bold cyan]\n"
                "Alternatively, you can use Hugging Face: [bold]--provider huggingface[/bold] with [bold]HF_TOKEN[/bold].",
                title="Configuration Required",
                border_style="red",
            )
        )
        sys.exit(1)

    if provider == "huggingface" and not Config.HUGGINGFACEHUB_API_TOKEN:
        console.print(
            Panel(
                "[bold red]Hugging Face Token Missing![/bold red]\n\n"
                "Please configure your HF token in [bold].env[/bold] or:\n"
                "  [bold]export HUGGINGFACEHUB_API_TOKEN=your_token_here[/bold]\n"
                "Get a token at: [bold cyan]https://huggingface.co/settings/tokens[/bold cyan]",
                title="Configuration Required",
                border_style="red",
            )
        )
        sys.exit(1)

    # Initialize LLM
    try:
        llm = get_llm(provider=provider, model_name=args.model)
    except Exception as e:
        console.print(f"[bold red]Failed to initialize LLM: {e}[/bold red]")
        sys.exit(1)

    # Interactive mode
    if args.interactive or not args.prompt:
        if not args.prompt:
            console.print(
                "[dim]No prompt provided on command line, launching interactive mode...[/dim]"
            )
        interactive_mode(llm)
        return

    # Direct prompt execution
    run_automation(prompt=args.prompt, llm=llm, verbose=not args.quiet)


if __name__ == "__main__":
    main()
