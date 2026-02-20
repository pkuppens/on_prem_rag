# Large Language Model (LLM) in RAG System

## Overview

This document describes the LLM implementation and configuration for the RAG system. The LLM is responsible for generating responses based on retrieved context and user queries, with a focus on on-premises deployment and data confidentiality.

## Table of Contents

1. [Introduction](#introduction)
2. [LLM Selection](#llm-selection)
3. [Implementation Details](#implementation-details)
4. [Performance Considerations](#performance-considerations)
5. [Future Improvements](#future-improvements)

## Introduction

The LLM is crucial for:

- Generating human-like responses
- Understanding user queries
- Synthesizing information from retrieved context
- Maintaining conversation coherence
- Ensuring data confidentiality
- Supporting multilingual interactions

## LLM Selection

### Current Implementation

- **Model**: Mistral 7B
- **Deployment**: Ollama (local)
- **Context Window**: 8K tokens
- **Temperature**: 0.2 - or even lower for running reproducible tests
- **Max Tokens**: 2048
- **Languages**: Multilingual support
- **License**: Apache 2.0

### Model Selection Criteria

1. **On-Premises Requirement**
   - Must run locally
   - No external API dependencies
   - Full data control

2. **Performance**
   - Adequate for RAG tasks
   - Reasonable resource requirements
   - Good response quality

3. **Multilingual Support**
   - Support for multiple languages
   - Consistent quality across languages
   - Good understanding of context

### Alternative Models Considered

1. **Llama 2**
   - Pros: Strong performance, good documentation
   - Cons: Larger resource requirements
   - Decision: Not selected due to size

2. **MPT-7B**
   - Pros: Good performance, smaller size
   - Cons: Limited language support
   - Decision: Not selected due to language coverage

## Implementation Details

### Integration with Ollama

```python
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from typing import List, Dict

def setup_llm(model_name: str = "mistral") -> Ollama:
    """Setup local LLM with Ollama."""
    return Ollama(
        model=model_name,
        temperature=0.7,
        context_window=8192,
        request_timeout=120.0
    )

# Configure global settings
Settings.llm = setup_llm()
```

### Query Processing

```python
def process_query(
    query: str,
    context: List[str],
    conversation_history: List[Dict[str, str]]
) -> str:
    """Process query with context and history."""
    # Format context for the model
    formatted_context = "\n\n".join(context)

    # Create system message
    system_message = (
        "You are a helpful assistant that answers questions based on the provided context. "
        "If the answer cannot be found in the context, say so. "
        "Use the conversation history to maintain context."
    )

    # Format messages for the model
    messages = [
        {"role": "system", "content": system_message},
        *conversation_history,
        {"role": "user", "content": f"Context: {formatted_context}\n\nQuestion: {query}"}
    ]

    # Get response from model
    response = Settings.llm.complete(messages)
    return response.text
```

### Configuration

- **System Prompt**: Customized for RAG context
- **Temperature**: 0.7 (balanced creativity and accuracy)
- **Max Tokens**: 2048 (response length limit)
- **Context Window**: 8192 tokens
- **Request Timeout**: 120 seconds

### Response Streaming

**Chat streaming** means the LLM provider sends partial results as they are generated, reducing perceived wait time. We pass through whatever the provider delivers (typically token- or sub-word chunks). We never simulate streaming—if the provider does not support streaming, callers use non-streaming `generate_answer()` instead. Streaming is independent of document retrieval.

### Environment Variables (LLM Backend Selection)

Switching backends is done via environment variables. The RAG pipeline uses LiteLLM for unified access.

| Variable          | Description                                                                | Default                  |
| ----------------- | -------------------------------------------------------------------------- | ------------------------ |
| `LLM_BACKEND`     | Backend: `ollama`, `openai`, `anthropic`, `azure`, `huggingface`, `gemini` | `ollama`                 |
| `LLM_MODEL`           | Global model override for all backends                                      | (backend-specific)       |
| `LLM_MODEL_GEMINI`    | Gemini model when `LLM_MODEL` not set                                       | `gemini-2.0-flash`      |
| `LLM_MODEL_OPENAI`    | OpenAI model when `LLM_MODEL` not set                                       | `gpt-4.1-mini`          |
| `LLM_MODEL_ANTHROPIC` | Anthropic model when `LLM_MODEL` not set                                    | `claude-sonnet-4-6`     |
| `LLM_MODEL_AZURE`     | Azure deployment name when `LLM_MODEL` not set (your deployment name)       | `gpt-4.1-mini`          |
| `OLLAMA_BASE_URL`     | Ollama API base URL                                                        | `http://localhost:11434` |
| `OLLAMA_MODEL`        | Legacy; used when `LLM_MODEL` not set and backend is ollama                | `mistral`               |

Provider-specific API keys (LiteLLM reads these):

| Backend       | Required env vars                                        |
| ------------- | -------------------------------------------------------- |
| `openai`      | `OPENAI_API_KEY`                                         |
| `anthropic`   | `ANTHROPIC_API_KEY`                                      |
| `azure`       | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`   |
| `huggingface` | `HUGGINGFACE_API_KEY` (optional for inference endpoints) |
| `gemini`      | `GEMINI_API_KEY`                                         |
| `ollama`      | None (local)                                             |

## Performance Considerations

### Optimization Strategies

1. **Prompt Engineering**
   - Optimize system prompts
   - Implement few-shot examples
   - Use chain-of-thought prompting

2. **Context Management**
   - Implement context window optimization
   - Use semantic compression
   - Prioritize relevant context

3. **Resource Management**
   - Monitor memory usage
   - Implement request queuing
   - Handle timeouts gracefully

## Future Improvements

### Planned Enhancements

1. **Model Updates**
   - Monitor for newer models
   - Evaluate performance improvements
   - Consider model quantization

2. **Performance**
   - Implement response caching
   - Optimize context handling
   - Add batch processing

3. **Quality Improvements**
   - Enhance prompt engineering
   - Implement better context selection
   - Add response validation

4. **Multilingual Support**
   - Improve language detection
   - Optimize for specific languages
   - Add language-specific prompts

## References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Mistral Model Card](https://huggingface.co/mistralai/Mistral-7B-v0.1)
- [LlamaIndex LLM Integration](https://docs.llamaindex.ai/en/stable/module_guides/llms/)

## Code Files

- [src/backend/rag_pipeline/config/llm_config.py](../../src/backend/rag_pipeline/config/llm_config.py) - LLM_BACKEND/LLM_MODEL config resolution
- [src/backend/rag_pipeline/core/llm_providers.py](../../src/backend/rag_pipeline/core/llm_providers.py) - Provider abstraction, LiteLLM integration, factory
- [src/rag_pipeline/core/db_query.py](../../src/rag_pipeline/core/db_query.py) - Placeholder NL2SQL pipeline used for database queries
- [src/backend/security/security_manager.py](../../src/backend/security/security_manager.py) - JWT token utilities used in authentication
