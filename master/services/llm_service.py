"""
LLM Service — multi-provider LLM abstraction layer.

Supports OpenAI API, Ollama (local), and other providers via a unified
interface. Used for scenario analysis, prompt refinement, and AI-assisted
shot planning.
"""

import os
import json
from typing import Optional, AsyncIterator
from enum import Enum
from dataclasses import dataclass, field

from ..utils import logger


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider = LLMProvider.MOCK
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = "You are a professional cinematography assistant."
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables."""
        provider_str = os.getenv("LLM_PROVIDER", "mock").lower()
        try:
            provider = LLMProvider(provider_str)
        except ValueError:
            logger.warning(f"Unknown LLM provider '{provider_str}', falling back to mock")
            provider = LLMProvider.MOCK

        return cls(
            provider=provider,
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            system_prompt=os.getenv(
                "LLM_SYSTEM_PROMPT",
                "You are a professional cinematography and film production assistant.",
            ),
        )


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    raw_response: Optional[dict] = None


class LLMService:
    """Unified LLM service supporting multiple providers."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self._config = config or LLMConfig.from_env()
        logger.info(
            f"LLMService initialized: provider={self._config.provider.value}, "
            f"model={self._config.model}"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        messages = [
            LLMMessage(role="system", content=system_prompt or self._config.system_prompt),
            LLMMessage(role="user", content=prompt),
        ]
        return await self.chat(messages, temperature, max_tokens)

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Send a chat completion request."""
        temp = temperature if temperature is not None else self._config.temperature
        tokens = max_tokens if max_tokens is not None else self._config.max_tokens

        if self._config.provider == LLMProvider.OPENAI:
            return await self._call_openai(messages, temp, tokens)
        elif self._config.provider == LLMProvider.OLLAMA:
            return await self._call_ollama(messages, temp, tokens)
        elif self._config.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(messages, temp, tokens)
        elif self._config.provider == LLMProvider.GEMINI:
            return await self._call_gemini(messages, temp, tokens)
        else:
            return self._mock_response(messages)

    async def _call_openai(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int,
    ) -> LLMResponse:
        """Call OpenAI-compatible API (also works with LM Studio, vLLM, etc.)."""
        try:
            import httpx
        except ImportError:
            logger.error("httpx is required for OpenAI provider. Install: pip install httpx")
            return self._mock_response(messages)

        url = self._config.base_url or "https://api.openai.com/v1"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.api_key or ''}",
        }
        payload = {
            "model": self._config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(
                    f"{url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data.get("model", self._config.model),
                    provider="openai",
                    usage=data.get("usage", {}),
                    raw_response=data,
                )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._mock_response(messages)

    async def _call_ollama(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int,
    ) -> LLMResponse:
        """Call Ollama local API."""
        try:
            import httpx
        except ImportError:
            logger.error("httpx is required for Ollama provider")
            return self._mock_response(messages)

        url = self._config.base_url or "http://localhost:11434"
        payload = {
            "model": self._config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(f"{url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()

                return LLMResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=data.get("model", self._config.model),
                    provider="ollama",
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                    raw_response=data,
                )
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return self._mock_response(messages)

    async def _call_anthropic(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int,
    ) -> LLMResponse:
        """Call Anthropic Claude API."""
        try:
            import httpx
        except ImportError:
            logger.error("httpx is required for Anthropic provider")
            return self._mock_response(messages)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._config.api_key or "",
            "anthropic-version": "2023-06-01",
        }

        # Separate system from user messages
        system_content = ""
        user_messages = []
        for m in messages:
            if m.role == "system":
                system_content = m.content
            else:
                user_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": self._config.model,
            "system": system_content,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

                content = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")

                return LLMResponse(
                    content=content,
                    model=data.get("model", self._config.model),
                    provider="anthropic",
                    usage=data.get("usage", {}),
                    raw_response=data,
                )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._mock_response(messages)

    async def _call_gemini(
        self, messages: list[LLMMessage], temperature: float, max_tokens: int,
    ) -> LLMResponse:
        """Call Google Gemini API."""
        try:
            import httpx
        except ImportError:
            logger.error("httpx is required for Gemini provider")
            return self._mock_response(messages)

        url = self._config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        model = self._config.model or "gemini-pro"

        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m.content}],
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                resp = await client.post(
                    f"{url}/models/{model}:generateContent",
                    headers={"x-goog-api-key": self._config.api_key or ""},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

                content = ""
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for p in parts:
                        content += p.get("text", "")

                return LLMResponse(
                    content=content,
                    model=model,
                    provider="gemini",
                    usage=data.get("usageMetadata", {}),
                    raw_response=data,
                )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._mock_response(messages)

    def _mock_response(self, messages: list[LLMMessage]) -> LLMResponse:
        """Return a mock response for testing or when no provider is configured."""
        last_user = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user = m.content
                break

        return LLMResponse(
            content=f"[MOCK] This is a mock LLM response. Configure LLM_PROVIDER "
                    f"environment variable to use a real provider. "
                    f"(Input was {len(last_user)} chars)",
            model="mock",
            provider="mock",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    # =========================================================================
    # HIGH-LEVEL HELPERS FOR PIPELINE
    # =========================================================================

    async def analyze_scenario(self, scenario_text: str) -> dict:
        """Analyze a scenario text and extract structured shot list data."""
        prompt = f"""Analyze the following film scenario and extract a structured shot list.
For each shot, provide:
- shot_number
- scene_description
- suggested_shot_size (EWS/WS/MS/MCU/CU/ECU)
- suggested_mood
- suggested_lighting
- key_action

Scenario:
{scenario_text}

Respond in JSON format as a list of shots."""

        response = await self.generate(
            prompt,
            system_prompt="You are a professional film director's assistant. "
                         "Analyze scenarios and create production-ready shot lists.",
        )

        try:
            # Try to parse JSON from response
            content = response.content
            # Find JSON array in response
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return {"shots": json.loads(content[start:end]), "raw": response.content}
        except json.JSONDecodeError:
            pass

        return {"shots": [], "raw": response.content, "parse_error": True}

    async def refine_prompt(
        self, base_prompt: str, style_reference: str = "", target_model: str = "flux"
    ) -> str:
        """Refine a base prompt for a specific generation model."""
        prompt = f"""Refine the following prompt for the {target_model} image generation model.
Make it more detailed and specific while maintaining the original intent.
Use comma-separated tags and descriptive phrases.

Base prompt: {base_prompt}
{f'Style reference: {style_reference}' if style_reference else ''}

Output only the refined prompt, no explanation."""

        response = await self.generate(
            prompt,
            system_prompt="You are a prompt engineering expert for AI image generation.",
            temperature=0.5,
        )
        return response.content.strip()
