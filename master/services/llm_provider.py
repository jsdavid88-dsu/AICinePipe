"""
LLM Provider Abstraction Layer — Multi-provider support.

Provides a unified interface for calling different LLM APIs:
- OpenAI (GPT-4o, GPT-4, etc.)
- Anthropic (Claude 3.5/4)
- Google Gemini (Gemini 2.0, etc.)
- OpenAI-compatible (LiteLLM, Ollama, vLLM, etc.)
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Provider Registry ───────────────────────────────────────────────────────

class LLMProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai_compatible"  # LiteLLM, Ollama, vLLM, etc.


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: str = "openai"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-4o"
    max_tokens: int = 16000
    temperature: float = 0.7
    # Gemini-specific
    project_id: Optional[str] = None
    location: Optional[str] = None


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: str
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    raw: Any = None


# ── Abstract Base Class ─────────────────────────────────────────────────────

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            system_prompt: System/instruction prompt
            user_prompt: User message
            json_mode: If True, request JSON-structured output
            
        Returns:
            LLMResponse with the generated content
        """
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is properly configured."""
        ...

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__


# ── OpenAI Provider ─────────────────────────────────────────────────────────

class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4o, GPT-4, etc.)"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        try:
            from openai import OpenAI
            api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
            if api_key:
                kwargs = {"api_key": api_key}
                if config.base_url:
                    kwargs["base_url"] = config.base_url
                self._client = OpenAI(**kwargs)
        except ImportError:
            logger.warning("openai package not installed: pip install openai")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def generate(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> LLMResponse:
        if not self.is_available:
            raise RuntimeError("OpenAI client not configured. Set api_key or OPENAI_API_KEY env var.")

        kwargs = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            raw=response,
        )


# ── Anthropic Provider ──────────────────────────────────────────────────────

class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude 3.5, Claude 4, etc.)"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        if not config.model or config.model.startswith("gpt"):
            config.model = "claude-sonnet-4-20250514"
        try:
            import anthropic
            api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.warning("anthropic package not installed: pip install anthropic")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def generate(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> LLMResponse:
        if not self.is_available:
            raise RuntimeError("Anthropic client not configured. Set api_key or ANTHROPIC_API_KEY env var.")

        # Anthropic doesn't have a native json_mode, so we add instructions
        effective_prompt = user_prompt
        if json_mode:
            effective_prompt += "\n\n[IMPORTANT: Your response MUST be valid JSON only. No markdown, no explanation, just the JSON object.]"

        response = self._client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": effective_prompt},
            ],
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            provider="anthropic",
            usage={
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
            },
            raw=response,
        )


# ── Google Gemini Provider ──────────────────────────────────────────────────

class GeminiProvider(LLMProvider):
    """Google Gemini API provider (Gemini 2.0, etc.)"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        if not config.model or config.model.startswith("gpt") or config.model.startswith("claude"):
            config.model = "gemini-2.0-flash"
        try:
            from google import genai
            api_key = config.api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if api_key:
                self._client = genai.Client(api_key=api_key)
        except ImportError:
            logger.warning("google-genai package not installed: pip install google-genai")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def generate(self, system_prompt: str, user_prompt: str,
                 json_mode: bool = False) -> LLMResponse:
        if not self.is_available:
            raise RuntimeError(
                "Gemini client not configured. Set api_key or GOOGLE_API_KEY env var. "
                "Install: pip install google-genai"
            )

        from google.genai import types

        config_kwargs = {
            "max_output_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system_instruction": system_prompt,
        }
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        response = self._client.models.generate_content(
            model=self.config.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        return LLMResponse(
            content=response.text,
            model=self.config.model,
            provider="gemini",
            usage={
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
            },
            raw=response,
        )


# ── OpenAI-Compatible Provider ──────────────────────────────────────────────

class OpenAICompatibleProvider(OpenAIProvider):
    """
    Any OpenAI-compatible API endpoint (LiteLLM, Ollama, vLLM, etc.)
    
    Uses the same OpenAI SDK but with a custom base_url.
    Examples:
      - Ollama: base_url="http://localhost:11434/v1", model="llama3"
      - vLLM:   base_url="http://localhost:8000/v1", model="meta-llama/Llama-3-8b"
      - LiteLLM: base_url="http://localhost:4000/v1"
    """

    def __init__(self, config: LLMConfig):
        if not config.base_url:
            config.base_url = "http://localhost:11434/v1"  # Ollama default
        if not config.api_key:
            config.api_key = "ollama"  # Placeholder for local APIs
        super().__init__(config)

    @property
    def provider_name(self) -> str:
        return f"OpenAI-Compatible ({self.config.base_url})"


# ── Factory ─────────────────────────────────────────────────────────────────

def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Factory function to create an LLM provider from config.
    
    Args:
        config: LLMConfig with provider type and credentials
        
    Returns:
        An initialized LLMProvider instance
        
    Raises:
        ValueError: If provider type is unknown
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "openai_compatible": OpenAICompatibleProvider,
        "ollama": OpenAICompatibleProvider,
        "litellm": OpenAICompatibleProvider,
        "vllm": OpenAICompatibleProvider,
    }

    provider_cls = providers.get(config.provider.lower())
    if not provider_cls:
        raise ValueError(
            f"Unknown LLM provider: {config.provider}. "
            f"Available: {', '.join(providers.keys())}"
        )

    provider = provider_cls(config)
    logger.info(f"Created LLM provider: {provider.provider_name} "
                f"(model={config.model}, available={provider.is_available})")
    return provider


def list_available_providers() -> List[Dict[str, Any]]:
    """List all supported LLM providers and their install status."""
    result = []

    # OpenAI
    try:
        import openai
        result.append({"id": "openai", "name": "OpenAI", "installed": True,
                       "models": ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
                       "env_key": "OPENAI_API_KEY"})
    except ImportError:
        result.append({"id": "openai", "name": "OpenAI", "installed": False,
                       "install": "pip install openai"})

    # Anthropic
    try:
        import anthropic
        result.append({"id": "anthropic", "name": "Anthropic", "installed": True,
                       "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                       "env_key": "ANTHROPIC_API_KEY"})
    except ImportError:
        result.append({"id": "anthropic", "name": "Anthropic", "installed": False,
                       "install": "pip install anthropic"})

    # Gemini
    try:
        from google import genai
        result.append({"id": "gemini", "name": "Google Gemini", "installed": True,
                       "models": ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"],
                       "env_key": "GOOGLE_API_KEY"})
    except ImportError:
        result.append({"id": "gemini", "name": "Google Gemini", "installed": False,
                       "install": "pip install google-genai"})

    # OpenAI-Compatible (always available if openai is installed)
    try:
        import openai
        result.append({"id": "openai_compatible", "name": "OpenAI-Compatible (Ollama/vLLM/LiteLLM)",
                       "installed": True, "models": ["any"],
                       "note": "Set base_url to your local endpoint"})
    except ImportError:
        result.append({"id": "openai_compatible", "name": "OpenAI-Compatible", "installed": False,
                       "install": "pip install openai"})

    return result
