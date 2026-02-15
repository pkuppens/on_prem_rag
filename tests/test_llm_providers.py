from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.rag_pipeline.core.llm_providers import (
    LLMProviderFactory,
    ModelNotFoundError,
    OllamaProvider,
)


def test_factory_creates_provider() -> None:
    """Test that the factory creates the correct provider type."""
    provider = LLMProviderFactory.create_provider("ollama", "mistral", {})
    assert isinstance(provider, OllamaProvider)


@patch("httpx.Client")
def test_ollama_generate_answer(mock_client_class) -> None:
    """Test that OllamaProvider generates answers correctly."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Hello! This is a test response from Ollama."}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    provider = OllamaProvider("mistral", {})
    result = provider.generate_answer("hello")

    assert "Ollama" in result or "test response" in result


@patch("httpx.Client")
def test_ollama_model_not_found_raises_model_not_found_error(mock_client_class) -> None:
    """As a user I want ModelNotFoundError when model is not pulled, so I know to run ollama pull.
    Technical: 404 response with 'not found' raises ModelNotFoundError with remediation.
    """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "model 'mistral:7b' not found"

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "model not found",
        request=MagicMock(),
        response=mock_response,
    )
    mock_client_class.return_value.__enter__.return_value = mock_client

    provider = OllamaProvider("mistral:7b", {"host": "http://localhost:11434"})

    with pytest.raises(ModelNotFoundError) as exc_info:
        provider.generate_answer("hello")

    assert exc_info.value.model_name == "mistral:7b"
    assert "ollama pull" in str(exc_info.value).lower()
