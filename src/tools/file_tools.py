"""File manipulation tools for the automation agent."""

import os
from pathlib import Path

from langchain_core.tools import tool

from src.config import Config


@tool
def write_file(filepath: str, content: str) -> str:
    """Write or overwrite text content to a file in the workspace.
    
    Args:
        filepath: Relative or absolute path to the file.
        content: Text content to write.
    """
    try:
        path = Path(filepath)
        if not path.is_absolute():
            path = Config.WORKSPACE_DIR / path

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {filepath}"
    except Exception as e:
        return f"Error writing file {filepath}: {e!s}"


@tool
def read_file(filepath: str) -> str:
    """Read and return content of a file from the workspace.
    
    Args:
        filepath: Relative or absolute path to the file.
    """
    try:
        path = Path(filepath)
        if not path.is_absolute():
            path = Config.WORKSPACE_DIR / path

        if not path.exists():
            return f"Error: File does not exist: {filepath}"
        
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file {filepath}: {e!s}"


@tool
def list_files(directory: str = ".") -> str:
    """List files and directories in the specified workspace path.
    
    Args:
        directory: Relative directory path to list (defaults to workspace root).
    """
    try:
        path = Path(directory)
        if not path.is_absolute():
            path = Config.WORKSPACE_DIR / path

        if not path.exists() or not path.is_dir():
            return f"Error: Directory does not exist: {directory}"

        entries = []
        for item in sorted(os.listdir(path)):
            if item.startswith(".") or item in ("__pycache__", "venv", ".git"):
                continue
            item_path = path / item
            kind = "DIR" if item_path.is_dir() else "FILE"
            size = f"({item_path.stat().st_size} bytes)" if item_path.is_file() else ""
            entries.append(f"[{kind}] {item} {size}".strip())

        return "\n".join(entries) if entries else "Directory is empty."
    except Exception as e:
        return f"Error listing directory {directory}: {e!s}"
