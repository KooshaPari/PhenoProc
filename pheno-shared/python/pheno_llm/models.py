"""Domain models for LLM interactions."""
from datetime import datetime
from enum import Enum
from typing import Optional

class Role(str, Enum):
    """Message role in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Provider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GROQ = "groq"
    MISTRAL = "mistral"
    COHERE = "cohere"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

class Message:
    """A single message in a conversation."""
    role: Role
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

    def __init__(
        self,
        role: Role | str,
        content: str,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ):
        self.role = Role(role) if isinstance(role, str) else role
        self.content = content
        self.name = name
        self.tool_call_id = tool_call_id

    def to_dict(self) -> dict:
        result = {"role": self.role.value, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result

class ToolCall:
    """A tool call made by the model."""
    id: str
    type: str
    function: dict

    def __init__(self, id: str, type: str = "function", function: Optional[dict] = None):
        self.id = id
        self.type = type
        self.function = function or {}

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "function": self.function}

class ToolDefinition:
    """Definition of a tool the model can call."""
    name: str
    description: str
    parameters: dict

    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_dict(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

class Usage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __init__(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: Optional[int] = None,
    ):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens or (prompt_tokens + completion_tokens)

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

class Response:
    """LLM response."""
    content: Optional[str]
    tool_calls: Optional[list[ToolCall]]
    tool_call_id: Optional[str]
    model: str
    provider: Provider
    usage: Optional[Usage]
    finish_reason: Optional[str]
    created: Optional[datetime]
    id: Optional[str]

    def __init__(
        self,
        content: Optional[str] = None,
        tool_calls: Optional[list[ToolCall]] = None,
        tool_call_id: Optional[str] = None,
        model: str = "unknown",
        provider: Provider | str = Provider.OPENAI,
        usage: Optional[Usage] = None,
        finish_reason: Optional[str] = None,
        created: Optional[datetime] = None,
        id: Optional[str] = None,
    ):
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id
        self.model = model
        self.provider = Provider(provider) if isinstance(provider, str) else provider
        self.usage = usage
        self.finish_reason = finish_reason
        self.created = created
        self.id = id

    def to_dict(self) -> dict:
        result = {"model": self.model, "provider": self.provider.value}
        if self.content:
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.usage:
            result["usage"] = self.usage.to_dict()
        if self.finish_reason:
            result["finish_reason"] = self.finish_reason
        if self.created:
            result["created"] = self.created.isoformat()
        if self.id:
            result["id"] = self.id
        return result

class CompletionRequest:
    """Request for text completion."""
    messages: list[Message]
    model: str
    provider: Provider | str
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    tools: Optional[list[ToolDefinition]] = None
    stream: bool = False

    def __init__(
        self,
        messages: list[Message],
        model: str,
        provider: Provider | str = Provider.OPENAI,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        tools: Optional[list[ToolDefinition]] = None,
        stream: bool = False,
    ):
        self.messages = messages
        self.model = model
        self.provider = Provider(provider) if isinstance(provider, str) else provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools
        self.stream = stream

    def to_dict(self) -> dict:
        result = {
            "messages": [m.to_dict() for m in self.messages],
            "model": self.model,
            "provider": self.provider.value if isinstance(self.provider, Provider) else self.provider,
            "temperature": self.temperature,
            "stream": self.stream,
        }
        if self.max_tokens:
            result["max_tokens"] = self.max_tokens
        if self.tools:
            result["tools"] = [t.to_dict() for t in self.tools]
        return result

class EmbeddingRequest:
    """Request for embeddings."""
    input: str | list[str]
    model: str
    provider: Provider | str

    def __init__(
        self,
        input: str | list[str],
        model: str,
        provider: Provider | str = Provider.OPENAI,
    ):
        self.input = input
        self.model = model
        self.provider = Provider(provider) if isinstance(provider, str) else provider

    def to_dict(self) -> dict:
        return {
            "input": self.input,
            "model": self.model,
            "provider": self.provider.value if isinstance(self.provider, Provider) else self.provider,
        }
