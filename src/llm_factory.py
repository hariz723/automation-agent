"""LLM Factory supporting Google Gemini and Hugging Face models."""

import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from src.config import Config


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """Instantiate and return the configured chat language model.
    
    Supports:
      - Google Gemini (default, highly recommended for tool use and speed)
      - Hugging Face (open-source models via Hugging Face Hub inference)
    
    Args:
        provider: 'gemini' or 'huggingface' (defaults to Config.LLM_PROVIDER)
        model_name: Specific model string (defaults to Config settings)
        temperature: Sampling temperature (defaults to Config.TEMPERATURE)
    """
    provider = (provider or Config.LLM_PROVIDER).lower().strip()
    temp = temperature if temperature is not None else Config.TEMPERATURE

    if provider == "gemini":
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "Gemini API key not found! Please set GEMINI_API_KEY or GOOGLE_API_KEY "
                "in your .env file or environment variables.\n"
                "Get a free key at: https://aistudio.google.com/"
            )

        from langchain_google_genai import ChatGoogleGenerativeAI

        model = model_name or Config.GEMINI_MODEL
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temp,
        )

    elif provider in ("huggingface", "hf"):
        token = Config.HUGGINGFACEHUB_API_TOKEN
        if not token:
            raise ValueError(
                "Hugging Face token not found! Please set HUGGINGFACEHUB_API_TOKEN or HF_TOKEN "
                "in your .env file or environment variables.\n"
                "Get an access token at: https://huggingface.co/settings/tokens"
            )

        from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

        repo_id = model_name or Config.HF_MODEL
        endpoint = HuggingFaceEndpoint(
            repo_id=repo_id,
            huggingfacehub_api_token=token,
            temperature=temp,
            max_new_tokens=2048,
        )
        return ChatHuggingFace(llm=endpoint)

    else:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. Please choose 'gemini' or 'huggingface'."
        )
