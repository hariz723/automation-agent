"""Linting and static analysis tool for the automation agent."""

import subprocess
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from src.config import Config


@tool
def lint_code(filepath_or_code: str) -> str:
    """Lint Python code or a Python file using Ruff to check for syntax errors and code smells.

    Args:
        filepath_or_code: Either a relative/absolute filepath to a .py file, or raw Python code string.
    """
    target = filepath_or_code.strip()

    # Check if target is an existing file
    candidate_path = Path(target)
    if not candidate_path.is_absolute():
        candidate_path = Config.WORKSPACE_DIR / candidate_path

    temp_file = None
    if candidate_path.exists() and candidate_path.is_file():
        file_to_check = str(candidate_path)
    else:
        # Treat as raw code string, write to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        )
        temp_file.write(target.rstrip() + "\n")
        temp_file.close()
        file_to_check = temp_file.name

    try:
        # Run ruff check
        result = subprocess.run(
            ["ruff", "check", file_to_check],
            capture_output=True,
            text=True,
            check=False,
        )

        output = []
        if result.returncode == 0:
            output.append("✅ Lint passed: No errors or warnings detected.")
        else:
            output.append("⚠️ Lint findings:")
            if result.stdout:
                output.append(result.stdout.strip())
            if result.stderr:
                output.append(result.stderr.strip())

        return "\n".join(output)

    except FileNotFoundError:
        # Fallback to python py_compile / syntax check if ruff is not in PATH
        import py_compile

        try:
            py_compile.compile(file_to_check, doraise=True)
            return "✅ Syntax check passed: Valid Python syntax."
        except py_compile.PyCompileError as e:
            return f"❌ Python Syntax Error:\n{e}"
    except Exception as e:
        return f"Error running linter: {e!s}"
    finally:
        if temp_file and Path(temp_file.name).exists():
            Path(temp_file.name).unlink(missing_ok=True)
