"""Provider-agnostic conversation layer for the tool loop.

SeismoForge's contract with a model is narrow: read a brief, call tools, read
what the tools return, decide the next move. Nothing in that contract is
vendor-specific, but the wire formats are - Anthropic carries tool results as
content blocks inside a user turn, OpenAI carries them as separate `tool`
messages keyed by call id, and the two describe tool schemas differently.

This module keeps that difference in one place. ``Conversation`` exposes the
loop the session actually needs (start, submit tool results, repeat) and each
provider subclass owns its own message history in its own native shape. The
session and the intake step never learn which vendor answered.

Nothing here reads a key from disk. Keys arrive as arguments or through the
environment, and are never logged, echoed, or written to an artifact.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

ANTHROPIC = "anthropic"
OPENAI = "openai"
PROVIDERS = (ANTHROPIC, OPENAI)

# Defaults chosen per provider when the caller does not name a model.
DEFAULT_MODELS = {ANTHROPIC: "claude-opus-5", OPENAI: "gpt-5.5"}

# Published prices per million tokens (input, output). Only models listed
# here get a cost figure; anything else reports tokens and says the price is
# not configured, rather than quoting a number nobody checked.
PRICES = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Reply:
    """One model turn, in the only shape the session cares about."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    refused: bool = False

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


def provider_for(model: str | None = None, api_key: str | None = None) -> str:
    """Infer the provider from whichever identifier we have."""
    if model:
        if model.startswith("claude"):
            return ANTHROPIC
        if model.startswith(("gpt", "o1", "o3", "o4", "chatgpt")):
            return OPENAI
    if api_key and api_key.startswith("sk-ant-"):
        return ANTHROPIC
    if api_key:
        return OPENAI
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ANTHROPIC
    if os.environ.get("OPENAI_API_KEY"):
        return OPENAI
    raise RuntimeError(
        "no model, key, or ANTHROPIC_API_KEY / OPENAI_API_KEY in the "
        "environment - cannot tell which provider to use"
    )


def estimate_cost(model: str, usage: dict[str, int]) -> float | None:
    """Cost in USD, or None when this model has no configured price."""
    price = PRICES.get(model)
    if price is None:
        return None
    price_in, price_out = price
    return round(
        (usage.get("input_tokens", 0) * price_in
         + usage.get("output_tokens", 0) * price_out) / 1_000_000,
        4,
    )


# ----------------------------------------------------------------------


class Conversation:
    """One model conversation over a fixed tool surface."""

    def __init__(
        self,
        *,
        system: str,
        tools: list[dict[str, Any]],
        model: str,
        api_key: str | None = None,
        max_tokens: int = 16000,
        force_tool: str | None = None,
    ) -> None:
        self.system = system
        self.tools = tools
        self.model = model
        self.max_tokens = max_tokens
        self.force_tool = force_tool
        self.usage = {"input_tokens": 0, "output_tokens": 0}
        self._setup(api_key)

    def _setup(self, api_key: str | None) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def start(self, user_text: str) -> Reply:  # pragma: no cover - abstract
        raise NotImplementedError

    def submit_tool_results(  # pragma: no cover - abstract
        self, results: list[dict[str, Any]]
    ) -> Reply:
        raise NotImplementedError

    @property
    def estimated_cost_usd(self) -> float | None:
        return estimate_cost(self.model, self.usage)


class AnthropicConversation(Conversation):
    def _setup(self, api_key: str | None) -> None:
        import anthropic

        self._sdk = anthropic
        self._client = (
            anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        )
        self._messages: list[dict[str, Any]] = []

    def _tools(self) -> list[dict[str, Any]]:
        return self.tools  # already in Anthropic shape

    def _send(self) -> Reply:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system,
            "tools": self._tools(),
            "messages": self._messages,
        }
        if self.force_tool:
            kwargs["tool_choice"] = {"type": "tool", "name": self.force_tool}
        response = self._client.messages.create(**kwargs)
        self.usage["input_tokens"] += response.usage.input_tokens
        self.usage["output_tokens"] += response.usage.output_tokens
        if response.stop_reason == "refusal":
            return Reply(refused=True)
        text = "".join(
            block.text for block in response.content
            if block.type == "text" and block.text.strip()
        )
        calls = [
            ToolCall(id=block.id, name=block.name, arguments=dict(block.input))
            for block in response.content if block.type == "tool_use"
        ]
        if calls:
            self._messages.append({"role": "assistant", "content": response.content})
        return Reply(text=text, tool_calls=calls)

    def start(self, user_text: str) -> Reply:
        self._messages.append({"role": "user", "content": user_text})
        return self._send()

    def submit_tool_results(self, results: list[dict[str, Any]]) -> Reply:
        self._messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": item["id"],
                        "content": item["content"],
                        **({"is_error": True} if item.get("is_error") else {}),
                    }
                    for item in results
                ],
            }
        )
        return self._send()


class OpenAIConversation(Conversation):
    def _setup(self, api_key: str | None) -> None:
        import openai

        self._sdk = openai
        self._client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()
        self._messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system}
        ]
        # Newer models take max_completion_tokens; older ones take max_tokens.
        # Settled on the first call rather than guessed from the model name.
        self._token_kwarg = "max_completion_tokens"

    def _tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool["input_schema"],
                },
            }
            for tool in self.tools
        ]

    def _send(self) -> Reply:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._messages,
            "tools": self._tools(),
        }
        if self.force_tool:
            kwargs["tool_choice"] = {
                "type": "function",
                "function": {"name": self.force_tool},
            }
        # Try the shape that worked last time first; fall back once, then
        # drop the parameter entirely. Anything that is not a complaint about
        # the token parameter is a real error and propagates.
        attempts = [self._token_kwarg] + [
            option for option in ("max_completion_tokens", "max_tokens", None)
            if option != self._token_kwarg
        ]
        for attempt in attempts:
            call = dict(kwargs)
            if attempt:
                call[attempt] = self.max_tokens
            try:
                response = self._client.chat.completions.create(**call)
                self._token_kwarg = attempt
                break
            except self._sdk.BadRequestError as error:
                if attempt is None or "token" not in str(error).lower():
                    raise
        if response.usage:
            self.usage["input_tokens"] += response.usage.prompt_tokens
            self.usage["output_tokens"] += response.usage.completion_tokens
        choice = response.choices[0]
        message = choice.message
        if getattr(message, "refusal", None):
            return Reply(refused=True)
        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=json.loads(call.function.arguments or "{}"),
            )
            for call in (message.tool_calls or [])
        ]
        if calls:
            self._messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in message.tool_calls
                    ],
                }
            )
        return Reply(text=message.content or "", tool_calls=calls)

    def start(self, user_text: str) -> Reply:
        self._messages.append({"role": "user", "content": user_text})
        return self._send()

    def submit_tool_results(self, results: list[dict[str, Any]]) -> Reply:
        for item in results:
            self._messages.append(
                {
                    "role": "tool",
                    "tool_call_id": item["id"],
                    "content": item["content"],
                }
            )
        return self._send()


def open_conversation(
    *,
    system: str,
    tools: list[dict[str, Any]],
    model: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
    max_tokens: int = 16000,
    force_tool: str | None = None,
) -> Conversation:
    """Start a conversation with whichever provider the inputs point at.

    Tool definitions are given in Anthropic shape (name / description /
    input_schema) and translated per provider, so the 9 tools are declared
    exactly once in ``agent/tools.py``.
    """
    provider = provider or provider_for(model, api_key)
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; expected one of {PROVIDERS}")
    model = model or DEFAULT_MODELS[provider]
    cls = AnthropicConversation if provider == ANTHROPIC else OpenAIConversation
    return cls(
        system=system, tools=tools, model=model, api_key=api_key,
        max_tokens=max_tokens, force_tool=force_tool,
    )
