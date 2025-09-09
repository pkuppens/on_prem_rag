"""Tests for the Question Answering system.

This module tests the Q&A functionality implemented in STORY-003.
It covers the core QA system, API endpoints, and LLM integration.

See STORY-003 for business context and acceptance criteria.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.rag_pipeline.api.app import app
from backend.rag_pipeline.core.llm_providers import OllamaProvider
from backend.rag_pipeline.core.qa_system import QASystem


class TestQASystem:
    """Test cases for the QASystem class."""

    def test_qa_system_initialization(self):
        """Test that QASystem initializes correctly with default LLM provider."""
        qa_system = QASystem()

        assert qa_system.llm_provider is not None
        assert isinstance(qa_system.llm_provider, OllamaProvider)
        assert qa_system.vector_store_manager is not None

    def test_qa_system_with_custom_llm_provider(self):
        """Test that QASystem accepts custom LLM provider."""
        mock_llm = Mock()
        qa_system = QASystem(llm_provider=mock_llm)

        assert qa_system.llm_provider is mock_llm

    def test_retrieve_relevant_chunks_empty_question(self):
        """Test that empty question raises ValueError."""
        qa_system = QASystem()

        with pytest.raises(ValueError, match="Question cannot be empty"):
            qa_system.retrieve_relevant_chunks("")

    def test_retrieve_relevant_chunks_whitespace_question(self):
        """Test that whitespace-only question raises ValueError."""
        qa_system = QASystem()

        with pytest.raises(ValueError, match="Question cannot be empty"):
            qa_system.retrieve_relevant_chunks("   ")

    @patch("backend.rag_pipeline.core.qa_system.query_embeddings")
    def test_retrieve_relevant_chunks_success(self, mock_query_embeddings):
        """Test successful chunk retrieval."""
        # Mock the query_embeddings function
        mock_query_embeddings.return_value = {
            "all_results": [
                {
                    "text": "Sample document content",
                    "similarity_score": 0.8,
                    "document_name": "test.pdf",
                    "chunk_index": 0,
                    "record_id": "123",
                    "page_number": 1,
                },
                {
                    "text": "Another document content",
                    "similarity_score": 0.6,
                    "document_name": "test2.pdf",
                    "chunk_index": 1,
                    "record_id": "124",
                    "page_number": 2,
                },
            ]
        }

        qa_system = QASystem()
        chunks = qa_system.retrieve_relevant_chunks("test question", top_k=5, similarity_threshold=0.5)

        assert len(chunks) == 2
        assert chunks[0]["similarity_score"] == 0.8
        assert chunks[1]["similarity_score"] == 0.6

    @patch("backend.rag_pipeline.core.qa_system.query_embeddings")
    def test_retrieve_relevant_chunks_with_threshold_filtering(self, mock_query_embeddings):
        """Test that similarity threshold filtering works correctly."""
        # Mock the query_embeddings function
        mock_query_embeddings.return_value = {
            "all_results": [
                {
                    "text": "High similarity content",
                    "similarity_score": 0.9,
                    "document_name": "test.pdf",
                    "chunk_index": 0,
                    "record_id": "123",
                    "page_number": 1,
                },
                {
                    "text": "Low similarity content",
                    "similarity_score": 0.5,
                    "document_name": "test2.pdf",
                    "chunk_index": 1,
                    "record_id": "124",
                    "page_number": 2,
                },
            ]
        }

        qa_system = QASystem()
        chunks = qa_system.retrieve_relevant_chunks("test question", similarity_threshold=0.7)

        # Only the high similarity chunk should be returned
        assert len(chunks) == 1
        assert chunks[0]["similarity_score"] == 0.9

    def test_generate_answer_empty_question(self):
        """Test that empty question raises ValueError."""
        qa_system = QASystem()
        mock_chunks = [{"text": "test", "document_name": "test.pdf"}]

        with pytest.raises(ValueError, match="Question cannot be empty"):
            qa_system.generate_answer("", mock_chunks)

    def test_generate_answer_no_context(self):
        """Test that empty context raises ValueError."""
        qa_system = QASystem()

        with pytest.raises(ValueError, match="Context chunks are required"):
            qa_system.generate_answer("test question", [])

    def test_generate_answer_success(self):
        """Test successful answer generation."""
        mock_llm = Mock()
        mock_llm.generate_answer.return_value = "This is a test answer."

        qa_system = QASystem(llm_provider=mock_llm)
        mock_chunks = [{"text": "Sample document content", "document_name": "test.pdf", "page_number": 1}]

        answer = qa_system.generate_answer("test question", mock_chunks)

        assert answer == "This is a test answer."
        mock_llm.generate_answer.assert_called_once()

        # Check that the prompt contains the context
        call_args = mock_llm.generate_answer.call_args[0][0]
        assert "Sample document content" in call_args
        assert "test question" in call_args

    def test_ask_question_empty_question(self):
        """Test that empty question raises ValueError."""
        qa_system = QASystem()

        with pytest.raises(ValueError, match="Question cannot be empty"):
            qa_system.ask_question("")

    @patch("backend.rag_pipeline.core.qa_system.query_embeddings")
    def test_ask_question_no_relevant_chunks(self, mock_query_embeddings):
        """Test handling when no relevant chunks are found."""
        mock_query_embeddings.return_value = {"all_results": []}

        qa_system = QASystem()
        result = qa_system.ask_question("test question")

        assert result["answer"] == "I couldn't find relevant information to answer your question."
        assert result["sources"] == []
        assert result["confidence"] == "low"
        assert result["chunks_retrieved"] == 0

    @patch("backend.rag_pipeline.core.qa_system.query_embeddings")
    def test_ask_question_success(self, mock_query_embeddings):
        """Test successful question answering."""
        # Mock the query_embeddings function
        mock_query_embeddings.return_value = {
            "all_results": [
                {
                    "text": "Sample document content about AI and machine learning",
                    "similarity_score": 0.9,
                    "document_name": "ai_guide.pdf",
                    "chunk_index": 0,
                    "record_id": "123",
                    "page_number": 1,
                }
            ]
        }

        mock_llm = Mock()
        mock_llm.generate_answer.return_value = "AI is a field of computer science."

        qa_system = QASystem(llm_provider=mock_llm)
        result = qa_system.ask_question("What is AI?")

        assert "AI is a field of computer science." in result["answer"]
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_name"] == "ai_guide.pdf"
        assert result["confidence"] == "high"
        assert result["chunks_retrieved"] == 1
        assert result["average_similarity"] == 0.9


class TestAskAPI:
    """Test cases for the /ask API endpoint."""

    def test_ask_endpoint_empty_question(self):
        """Test that empty question returns validation error."""
        client = TestClient(app)

        response = client.post("/api/ask", json={"question": ""})

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_ask_endpoint_missing_question(self):
        """Test that missing question field returns validation error."""
        client = TestClient(app)

        response = client.post("/api/ask", json={})

        assert response.status_code == 422  # Validation error

    def test_ask_endpoint_invalid_top_k(self):
        """Test that invalid top_k values return validation error."""
        client = TestClient(app)

        # Test negative top_k
        response = client.post("/api/ask", json={"question": "test", "top_k": -1})
        assert response.status_code == 422

        # Test top_k too large
        response = client.post("/api/ask", json={"question": "test", "top_k": 100})
        assert response.status_code == 422

    def test_ask_endpoint_invalid_similarity_threshold(self):
        """Test that invalid similarity threshold returns validation error."""
        client = TestClient(app)

        # Test negative threshold
        response = client.post("/api/ask", json={"question": "test", "similarity_threshold": -0.1})
        assert response.status_code == 422

        # Test threshold > 1
        response = client.post("/api/ask", json={"question": "test", "similarity_threshold": 1.1})
        assert response.status_code == 422

    @patch("backend.rag_pipeline.api.ask.qa_system")
    def test_ask_endpoint_success(self, mock_qa_system):
        """Test successful question answering via API."""
        # Mock the QA system response
        mock_qa_system.ask_question.return_value = {
            "answer": "This is a test answer.",
            "sources": [
                {"document_name": "test.pdf", "page_number": 1, "similarity_score": 0.9, "text_preview": "Sample content..."}
            ],
            "confidence": "high",
            "chunks_retrieved": 1,
            "average_similarity": 0.9,
        }

        client = TestClient(app)
        response = client.post("/api/ask", json={"question": "What is AI?"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a test answer."
        assert len(data["sources"]) == 1
        assert data["confidence"] == "high"
        assert data["chunks_retrieved"] == 1

    def test_ask_health_endpoint(self):
        """Test the health check endpoint."""
        client = TestClient(app)

        with patch("backend.rag_pipeline.api.ask.qa_system.llm_provider.health_check", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True

            response = client.get("/api/ask/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["llm_provider"] == "available"


class TestOllamaProvider:
    """Test cases for the OllamaProvider class."""

    def test_ollama_provider_initialization(self):
        """Test that OllamaProvider initializes correctly."""
        provider = OllamaProvider("mistral:7b", {"host": "http://localhost:11434"})

        assert provider.model_name == "mistral:7b"
        assert provider.host == "http://localhost:11434"

    def test_ollama_provider_default_host(self):
        """Test that OllamaProvider uses default host when not specified."""
        provider = OllamaProvider("mistral:7b", {})

        assert provider.host == "http://localhost:11434"

    @patch("httpx.Client")
    def test_ollama_generate_answer_success(self, mock_client_class):
        """Test successful answer generation with Ollama."""
        # Mock the HTTP client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"response": "This is a test answer."}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        provider = OllamaProvider("mistral:7b", {})
        answer = provider.generate_answer("What is AI?")

        assert answer == "This is a test answer."
        mock_client.post.assert_called_once()

    @patch("httpx.Client")
    def test_ollama_generate_answer_connection_error(self, mock_client_class):
        """Test handling of connection errors."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("Connection failed")
        mock_client_class.return_value.__enter__.return_value = mock_client

        provider = OllamaProvider("mistral:7b", {})

        with pytest.raises(RuntimeError, match="Unexpected error during answer generation"):
            provider.generate_answer("What is AI?")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_ollama_health_check_success(self, mock_client_class):
        """Test successful health check."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get = Mock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        provider = OllamaProvider("mistral:7b", {})
        is_healthy = await provider.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_ollama_health_check_failure(self, mock_client_class):
        """Test health check failure."""
        mock_client = Mock()
        mock_client.get = Mock(side_effect=Exception("Connection failed"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        provider = OllamaProvider("mistral:7b", {})
        is_healthy = await provider.health_check()

        assert is_healthy is False
