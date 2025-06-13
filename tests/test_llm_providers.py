from backend.rag_pipeline.core.llm_providers import (
    LLMProviderFactory,
    OllamaProvider,
)


def test_factory_creates_provider() -> None:
    provider = LLMProviderFactory.create_provider("ollama", "mistral", {})
    assert isinstance(provider, OllamaProvider)
    assert "Ollama" in provider.generate_answer("hello")
