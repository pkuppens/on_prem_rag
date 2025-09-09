from unittest.mock import patch

from backend.rag_pipeline.core.llm_providers import (
    LLMProviderFactory,
    OllamaProvider,
)


def test_factory_creates_provider() -> None:
    """Test that the factory creates the correct provider type."""
    provider = LLMProviderFactory.create_provider("ollama", "mistral", {})
    assert isinstance(provider, OllamaProvider)


@patch("httpx.Client.post")
def test_ollama_generate_answer(mock_post) -> None:
    """Test that OllamaProvider generates answers correctly."""
    # Mock the HTTP response
    mock_response = {"response": "Hello! This is a test response from Ollama."}
    mock_post.return_value.json.return_value = mock_response
    mock_post.return_value.raise_for_status.return_value = None

    provider = OllamaProvider("mistral", {})
    result = provider.generate_answer("hello")

    assert "Ollama" in result or "test response" in result
