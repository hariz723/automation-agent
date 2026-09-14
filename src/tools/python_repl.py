"""Python execution sandbox tool for the automation agent."""

import io
import sys
import traceback

from langchain_core.tools import tool


@tool
def execute_python(code: str) -> str:
    """Execute Python code in an isolated execution namespace and return stdout/output.
    Use this tool to compute values, transform data, generate structured files, scrape, or automate tasks.

    Args:
        code: Complete, valid Python code to execute.
    """
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    # Shared execution namespace
    exec_globals: dict = {
        "__builtins__": __builtins__,
    }

    try:
        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer
        exec(code, exec_globals)
        output = stdout_buffer.getvalue()
        errors = stderr_buffer.getvalue()

        result_parts = []
        if output:
            result_parts.append(f"STDOUT:\n{output.strip()}")
        if errors:
            result_parts.append(f"STDERR:\n{errors.strip()}")

        if not result_parts:
            return "Code executed successfully with no output."
        return "\n\n".join(result_parts)

    except Exception:
        tb = traceback.format_exc()
        return f"Execution failed with Exception:\n{tb}"
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
