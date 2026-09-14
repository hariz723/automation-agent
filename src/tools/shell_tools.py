"""Shell execution tool for the automation agent."""

import subprocess

from langchain_core.tools import tool

from src.config import Config


@tool
def execute_shell(command: str) -> str:
    """Execute a bash shell command in the project workspace and return the stdout and stderr.
    Use this to run scripts, CLI utilities, git commands, or check system output.

    Args:
        command: The shell command line string to run.
    """
    # Safety filter: prevent destructive global commands
    forbidden_patterns = [
        "rm -rf /",
        "mkfs",
        ":(){ :|:& };:",
        "shutdown",
        "reboot",
        "dd if=",
    ]
    for pattern in forbidden_patterns:
        if pattern in command:
            return f"Error: Command blocked for safety: '{pattern}' is not allowed."

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(Config.WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=Config.TIMEOUT_SECONDS,
        )

        output_parts = []
        if proc.stdout:
            output_parts.append(f"STDOUT:\n{proc.stdout.strip()}")
        if proc.stderr:
            output_parts.append(f"STDERR:\n{proc.stderr.strip()}")
        output_parts.append(f"Return Code: {proc.returncode}")

        return "\n\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {Config.TIMEOUT_SECONDS} seconds."
    except Exception as e:
        return f"Shell execution error: {str(e)}"
