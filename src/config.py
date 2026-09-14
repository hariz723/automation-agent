"""Configuration management for the AI Automation Agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration settings."""

    # LLM Provider: 'gemini' or 'huggingface'
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    # Google Gemini Keys & Model
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Hugging Face Token & Model
    HUGGINGFACEHUB_API_TOKEN: str = os.getenv("HUGGINGFACEHUB_API_TOKEN", "") or os.getenv(
        "HF_TOKEN", ""
    )
    HF_MODEL: str = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")

    # Execution limits
    MAX_STEP_RETRIES: int = int(os.getenv("MAX_STEP_RETRIES", "2"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "120"))

    # Workspace directory for tool execution
    WORKSPACE_DIR: Path = Path(__file__).resolve().parent.parent

    @classmethod
    def validate(cls) -> dict:
        """Validate current configuration and return status dictionary."""
        status = {
            "provider": cls.LLM_PROVIDER,
            "has_gemini_key": bool(cls.GEMINI_API_KEY),
            "gemini_model": cls.GEMINI_MODEL,
            "has_hf_token": bool(cls.HUGGINGFACEHUB_API_TOKEN),
            "hf_model": cls.HF_MODEL,
            "workspace_dir": str(cls.WORKSPACE_DIR),
        }
        return status
