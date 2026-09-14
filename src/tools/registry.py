"""Unified tool registry for the automation agent."""

from langchain_core.tools import BaseTool

from src.tools.file_tools import list_files, read_file, write_file
from src.tools.lint_tools import lint_code
from src.tools.python_repl import execute_python
from src.tools.shell_tools import execute_shell
from src.tools.web_tools import fetch_webpage, web_search

# Full list of available tools for agent invocation
ALL_TOOLS: list[BaseTool] = [
    write_file,
    read_file,
    list_files,
    lint_code,
    execute_python,
    web_search,
    fetch_webpage,
    execute_shell,
]

# Tool lookup dictionary by name
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def get_tools() -> list[BaseTool]:
    """Return list of all registered tools."""
    return ALL_TOOLS


def get_tool_descriptions() -> str:
    """Return formatted descriptions of all tools for prompting."""
    descriptions = []
    for tool in ALL_TOOLS:
        descriptions.append(f"- **{tool.name}**: {tool.description}")
    return "\n".join(descriptions)
