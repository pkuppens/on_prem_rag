"""Conversational chat API endpoint for the RAG pipeline.

Implements POST /api/chat with message history for multi-turn RAG conversations.
Supports streaming via POST /api/chat/stream (SSE).

Chat streaming: the LLM provider delivers partial results as they are generated,
reducing perceived wait time. We pass through provider chunks; we never simulate
streaming (that would not reduce wait). Streaming is independent of document retrieval.
"""

import json
from collections.abc import Generator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..config.llm_config import get_llm_config
from ..core.qa_system import QASystem
from ..utils.logging import StructuredLogger
from .metrics import get_metrics

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

qa_system = QASystem()


class ChatMessage(BaseModel):
    """Single message in a conversation."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request payload for the chat endpoint."""

    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Conversation history. Last message should be from user.",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    direct: bool = Field(
        default=False,
        description="When True (stream only), skip RAG retrieval and stream LLM response directly for the question.",
    )


def _format_sse(data: dict) -> str:
    """Format dict as SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


class ChatResponse(BaseModel):
    """Response payload for the chat endpoint."""

    answer: str
    sources: list[dict]
    confidence: str
    chunks_retrieved: int
    average_similarity: float


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Conversational RAG: answer with message history context.

    Uses the last user message for retrieval. Prior messages provide context
    for the LLM to generate coherent multi-turn responses.

    Args:
        payload: Chat request with messages and optional parameters

    Returns:
        ChatResponse with answer and sources

    Raises:
        HTTPException: If last message is not from user or processing fails
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="At least one message is required")

    last_msg = payload.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")

    question = last_msg.content.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Last message content must not be empty")

    try:
        get_metrics().record_query()
        llm_config = get_llm_config()
        logger.info("Chat query", question=question, llm_backend=llm_config.backend_model_pair)

        # Build conversation history for context (exclude current question)
        history = [{"role": m.role, "content": m.content} for m in payload.messages[:-1]]

        # Retrieve chunks for current question
        chunks = qa_system.retrieve_relevant_chunks(
            question,
            top_k=payload.top_k,
            similarity_threshold=payload.similarity_threshold,
        )

        if not chunks:
            return ChatResponse(
                answer="I couldn't find relevant information to answer your question.",
                sources=[],
                confidence="low",
                chunks_retrieved=0,
                average_similarity=0.0,
            )

        # Generate answer with conversation history
        answer = qa_system.generate_answer(question, chunks, conversation_history=history if history else None)

        sources = [
            {
                "document_name": c["document_name"],
                "page_number": c.get("page_number", "unknown"),
                "similarity_score": c["similarity_score"],
                "text_preview": (c["text"][:200] + "...") if len(c["text"]) > 200 else c["text"],
            }
            for c in chunks
        ]

        avg_sim = sum(c["similarity_score"] for c in chunks) / len(chunks)
        confidence = "high" if avg_sim > 0.8 else "medium" if avg_sim > 0.6 else "low"

        return ChatResponse(
            answer=answer.strip(),
            sources=sources,
            confidence=confidence,
            chunks_retrieved=len(chunks),
            average_similarity=avg_sim,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Chat failed", question=question, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}") from e


def _stream_chat_response(
    question: str,
    history: list[dict],
    top_k: int,
    similarity_threshold: float,
    *,
    direct: bool = False,
) -> Generator[str, None, None]:
    """Yield SSE events for streaming chat response."""
    llm_config = get_llm_config()
    logger.info("Chat stream started", question=question, backend=llm_config.backend_model_pair, direct=direct)

    if direct:
        yield _format_sse({"type": "sources", "sources": [], "chunks_retrieved": 0, "direct": True})
        try:
            stream_method = getattr(qa_system.llm_provider, "generate_answer_stream", None)
            if callable(stream_method):
                prompt = question
                if history:
                    history_text = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history[-4:])
                    prompt = f"Prior conversation:\n{history_text}\n\nUser: {question}\n\nAssistant:"
                for token in stream_method(prompt):
                    yield _format_sse({"type": "token", "content": token})
            else:
                answer = qa_system.llm_provider.generate_answer(question)
                yield _format_sse({"type": "answer", "content": answer})
        except Exception as e:
            logger.error("Direct stream failed", error=str(e))
            yield _format_sse({"type": "answer", "content": f"Error: {e}"})
        yield _format_sse({"type": "done"})
        return

    chunks = qa_system.retrieve_relevant_chunks(question, top_k=top_k, similarity_threshold=similarity_threshold)
    if not chunks:
        yield _format_sse({"type": "answer", "content": "I couldn't find relevant information to answer your question."})
        yield _format_sse({"type": "sources", "sources": [], "chunks_retrieved": 0})
        yield _format_sse({"type": "done"})
        return

    sources = [
        {
            "document_name": c["document_name"],
            "page_number": c.get("page_number", "unknown"),
            "similarity_score": c["similarity_score"],
            "text_preview": (c["text"][:200] + "...") if len(c["text"]) > 200 else c["text"],
        }
        for c in chunks
    ]
    yield _format_sse({"type": "sources", "sources": sources, "chunks_retrieved": len(chunks)})

    try:
        for token in qa_system.generate_answer_stream(question, chunks, conversation_history=history if history else None):
            yield _format_sse({"type": "token", "content": token})
    except NotImplementedError:
        answer = qa_system.generate_answer(question, chunks, conversation_history=history if history else None)
        yield _format_sse({"type": "answer", "content": answer})
    yield _format_sse({"type": "done"})


@router.post("/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    """Stream chat response as Server-Sent Events (SSE).

    Events: sources (metadata), token (partial answer), done.
    Set direct=true to skip RAG retrieval and stream LLM response directly (for testing streaming).
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="At least one message is required")
    last_msg = payload.messages[-1]
    if last_msg.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")
    question = last_msg.content.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Last message content must not be empty")

    get_metrics().record_query()
    history = [{"role": m.role, "content": m.content} for m in payload.messages[:-1]]

    return StreamingResponse(
        _stream_chat_response(
            question,
            history,
            top_k=payload.top_k,
            similarity_threshold=payload.similarity_threshold,
            direct=payload.direct,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
