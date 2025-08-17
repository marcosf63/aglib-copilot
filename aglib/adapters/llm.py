from __future__ import annotations
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    messages: List[LLMMessage]
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int] = field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMAdapter(ABC):
    def __init__(self, model: str = "gpt-3.5-turbo", **config):
        self.model = model
        self.config = config
        self._client = None

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        pass

    @abstractmethod
    async def _initialize_client(self):
        pass

    async def ask(self, prompt: str, **kwargs) -> str:
        """Backward compatibility method"""
        messages = [LLMMessage(role="user", content=prompt)]
        request = LLMRequest(messages=messages, model=self.model, **kwargs)
        response = await self.complete(request)
        return response.content


class OpenAIAdapter(LLMAdapter):
    def __init__(self, model: str = "gpt-3.5-turbo", **config):
        super().__init__(model, **config)
        self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")

    async def _initialize_client(self):
        if self._client is None:
            try:
                import openai

                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._initialize_client()

        try:
            messages = [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ]

            kwargs = {
                "model": request.model or self.model,
                "messages": messages,
                "temperature": request.temperature,
            }

            if request.max_tokens:
                kwargs["max_tokens"] = request.max_tokens

            if request.tools:
                kwargs["tools"] = request.tools
                kwargs["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**kwargs)

            content = ""
            tool_calls = []

            if response.choices[0].message.content:
                content = response.choices[0].message.content

            if response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "id": call.id,
                        "function": call.function.name,
                        "arguments": call.function.arguments,
                    }
                    for call in response.choices[0].message.tool_calls
                ]

            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": (
                    response.usage.completion_tokens if response.usage else 0
                ),
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            return LLMResponse(
                content=content,
                usage=usage,
                tool_calls=tool_calls,
                metadata={
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                },
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-3-haiku-20240307", **config):
        super().__init__(model, **config)
        self.api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found")

    async def _initialize_client(self):
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._initialize_client()

        try:
            # Convert messages to Anthropic format
            system_message = ""
            messages = []

            for msg in request.messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    messages.append({"role": msg.role, "content": msg.content})

            kwargs = {
                "model": request.model or self.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens or 2000,
            }

            if system_message:
                kwargs["system"] = system_message

            response = await self._client.messages.create(**kwargs)

            content = ""
            if response.content and len(response.content) > 0:
                content = response.content[0].text

            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            }

            return LLMResponse(
                content=content,
                usage=usage,
                tool_calls=[],  # Tool calls not implemented for Anthropic yet
                metadata={"model": response.model, "stop_reason": response.stop_reason},
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class LocalAdapter(LLMAdapter):
    def __init__(self, model: str = "llama2", **config):
        super().__init__(model, **config)
        self.base_url = config.get("base_url") or os.getenv(
            "LOCAL_LLM_URL", "http://localhost:11434"
        )

    async def _initialize_client(self):
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await self._initialize_client()

        try:
            # Format for Ollama API
            prompt = ""
            for msg in request.messages:
                if msg.role == "system":
                    prompt += f"System: {msg.content}\n"
                elif msg.role == "user":
                    prompt += f"User: {msg.content}\n"
                elif msg.role == "assistant":
                    prompt += f"Assistant: {msg.content}\n"

            prompt += "Assistant: "

            payload = {
                "model": request.model or self.model,
                "prompt": prompt,
                "temperature": request.temperature,
                "stream": False,
            }

            if request.max_tokens:
                payload["options"] = {"num_predict": request.max_tokens}

            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()

            data = response.json()
            content = data.get("response", "")

            return LLMResponse(
                content=content,
                usage={"total_tokens": len(content.split())},  # Rough estimate
                tool_calls=[],
                metadata={"model": data.get("model", self.model)},
            )

        except Exception as e:
            logger.error(f"Local LLM API error: {e}")
            raise


class LLMFactory:
    @staticmethod
    def create(
        provider: Union[str, LLMProvider], model: str = None, **config
    ) -> LLMAdapter:
        if isinstance(provider, str):
            provider = LLMProvider(provider)

        if provider == LLMProvider.OPENAI:
            return OpenAIAdapter(model or "gpt-3.5-turbo", **config)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicAdapter(model or "claude-3-haiku-20240307", **config)
        elif provider == LLMProvider.LOCAL:
            return LocalAdapter(model or "llama2", **config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


class LLMWithFallback(LLMAdapter):
    def __init__(self, primary: LLMAdapter, fallback: LLMAdapter):
        self.primary = primary
        self.fallback = fallback
        super().__init__(primary.model)

    async def _initialize_client(self):
        await self.primary._initialize_client()
        await self.fallback._initialize_client()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            return await self.primary.complete(request)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}, trying fallback")
            try:
                return await self.fallback.complete(request)
            except Exception as fallback_error:
                logger.error(f"Fallback LLM also failed: {fallback_error}")
                # Return a basic response to keep system functional
                return LLMResponse(
                    content="I apologize, but I'm experiencing technical difficulties. Please try again later.",
                    usage={},
                    tool_calls=[],
                    metadata={"error": "both_llms_failed"},
                )


# Backward compatibility
class LLM(LLMAdapter):
    def __init__(self, provider: str = "openai", model: str = None, **config):
        self._adapter = LLMFactory.create(provider, model, **config)
        super().__init__(self._adapter.model, **config)

    async def _initialize_client(self):
        await self._adapter._initialize_client()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return await self._adapter.complete(request)

    async def ask(self, prompt: str, **kwargs) -> str:
        return await self._adapter.ask(prompt, **kwargs)
