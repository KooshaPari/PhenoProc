"""LLM Router - Routes requests to appropriate providers."""
from typing import Optional
from pheno_llm.models import Provider, CompletionRequest, EmbeddingRequest, Response, Message

class LLMRouter:
    """Routes LLM requests to appropriate providers."""

    def __init__(self, default_provider: Provider = Provider.OPENAI):
        self.default_provider = default_provider
        self._providers: dict[Provider, dict] = {}

    def add_provider(self, provider: Provider, config: dict) -> None:
        """Add provider configuration."""
        self._providers[provider] = config

    async def complete(self, request: CompletionRequest) -> Response:
        """Route completion request to appropriate provider."""
        provider = request.provider
        # Placeholder - actual implementation would call the provider
        raise NotImplementedError(f"Provider {provider} not configured")

    async def embed(self, request: EmbeddingRequest) -> list[list[float]]:
        """Route embedding request to appropriate provider."""
        raise NotImplementedError(f"Embedding not implemented")

_router: Optional[LLMRouter] = None

def get_router() -> LLMRouter:
    """Get or create the global router instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router

async def route_llm(request: CompletionRequest) -> Response:
    """Route an LLM request to the appropriate provider."""
    router = get_router()
    return await router.complete(request)
