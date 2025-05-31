# Goal 3: Modular LLM Integration

## Context from Business Objective

This goal ensures flexibility and future-proofing of AI capabilities by implementing a modular LLM architecture. The business requires the ability to switch between different models and providers while maintaining consistent performance and supporting various deployment scenarios.

## Objective

Build a configurable LLM provider system that supports multiple backends (Ollama, llama.cpp, HuggingFace) with consistent interfaces, custom prompt templates, and performance benchmarking capabilities. This enables future model upgrades without architectural changes.

## Core Features

- Configurable model backends (Ollama, llama.cpp, HuggingFace)
- Default Mistral 7B with Apache 2.0 license
- Custom prompt templates per model
- Performance benchmarking and monitoring
- Model switching without downtime
- Resource optimization per model type

## Business Impact

**Ensure flexibility and future-proofing of AI capabilities**

### Strategic Value
- **Vendor Independence**: Avoid lock-in to specific model providers
- **Performance Optimization**: Choose best model for each use case
- **Cost Management**: Balance performance vs resource requirements
- **Future-Proofing**: Easy integration of new models as they emerge

### Technical Benefits
- **Scalability**: Different models for different workloads
- **Reliability**: Fallback options if primary model fails
- **Optimization**: GPU/CPU resource management per model
- **Monitoring**: Performance tracking across model types

## Technical Implementation

### Model Provider Interface

**Core Abstraction**:

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_answer(self, prompt: str) -> str:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str = "mistral:7b"):
        self.model = model_name
        
    def generate_answer(self, prompt: str) -> str:
        # Ollama API call
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
```

### Supported Backends

| Backend | Use Case | Performance | Resource Requirements |
|---------|----------|-------------|----------------------|
| **Ollama** | Primary deployment | High | Medium (8GB+ RAM) |
| **llama.cpp** | CPU-only environments | Medium | Low (4GB+ RAM) |
| **HuggingFace** | Development/testing | Variable | High (GPU recommended) |
| **vLLM** | High-throughput production | Very High | High (GPU required) |

## Model Selection Strategy

### Default Model: Mistral 7B

**Selection Rationale**:
- **License**: Apache 2.0 (commercial use allowed)
- **Performance**: Excellent quality-to-size ratio
- **Resource Efficiency**: Runs well on consumer hardware
- **Multilingual**: Good support for multiple languages
- **Community**: Strong ecosystem and fine-tuning resources

### Alternative Models

| Model | Size | License | Use Case | Commercial Ready |
|-------|------|---------|----------|------------------|
| **Llama 3.1 8B** | 8B | Custom Commercial | Primary alternative | ✅ Yes |
| **Phi-3 Mini** | 3.8B | MIT | Resource-constrained environments | ✅ Yes |
| **Gemma 2 9B** | 9B | Custom | High-performance option | ⚠️ Limited commercial use |
| **Qwen 2.5 7B** | 7B | Apache 2.0 | Multilingual focus | ✅ Yes |

## Architecture Design

### Provider Factory Pattern

```python
class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        model_name: str,
        config: dict
    ) -> LLMProvider:
        """Create provider instance based on type."""
        
        if provider_type == "ollama":
            return OllamaProvider(model_name, config)
        elif provider_type == "llamacpp":
            return LlamaCppProvider(model_name, config)
        elif provider_type == "huggingface":
            return HuggingFaceProvider(model_name, config)
        else:
            raise ValueError(f"Unknown provider: {provider_type}")

class LLMManager:
    """Manages multiple LLM providers with failover."""
    
    def __init__(self, config: dict):
        self.providers = []
        self.active_provider = None
        self.config = config
        self._load_providers()
    
    def generate_answer(self, prompt: str) -> str:
        """Generate answer with automatic failover."""
        for provider in self.providers:
            try:
                return provider.generate_answer(prompt)
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue
        
        raise RuntimeError("All providers failed")
```

### Configuration Management

```yaml
# config/llm_config.yaml
llm:
  providers:
    - type: "ollama"
      model: "mistral:7b"
      endpoint: "http://localhost:11434"
      timeout: 30
      max_tokens: 4000
      temperature: 0.1
      
    - type: "llamacpp"
      model: "models/mistral-7b-q4.gguf"
      n_ctx: 4096
      n_threads: 8
      temperature: 0.1
      
  fallback_order: ["ollama", "llamacpp"]
  
  prompt_templates:
    rag_query: |
      Context: {context}
      
      Question: {question}
      
      Answer based on the context above. If the context doesn't contain 
      relevant information, say "I don't have enough information to answer this question."
      
      Answer:
    
    summarization: |
      Summarize the following text in 2-3 sentences:
      
      {text}
      
      Summary:
```

## Implementation Tasks

### Task 3.1: Provider Abstraction Layer
- Define LLMProvider interface
- Implement provider factory pattern
- Configuration management system
- Error handling and failover logic

### Task 3.2: Backend Implementations
- Ollama provider with API integration
- llama.cpp provider with Python bindings
- HuggingFace provider with transformers library
- Provider-specific optimizations

### Task 3.3: Prompt Engineering System
- Template management system
- Model-specific prompt optimization
- A/B testing framework for prompts
- Performance measurement tools

### Task 3.4: Model Management
- Model download and installation
- Version management
- Resource monitoring
- Performance benchmarking

## Prompt Engineering

### Template System

```python
class PromptTemplate:
    """Manages prompt templates for different models."""
    
    def __init__(self, template: str, model_type: str):
        self.template = template
        self.model_type = model_type
        
    def format(self, **kwargs) -> str:
        """Format template with provided variables."""
        return self.template.format(**kwargs)

class PromptManager:
    """Manages prompts for different models and use cases."""
    
    def __init__(self):
        self.templates = {}
        self._load_templates()
    
    def get_prompt(
        self, 
        use_case: str, 
        model_type: str, 
        **kwargs
    ) -> str:
        """Get formatted prompt for specific use case and model."""
        
        template_key = f"{use_case}_{model_type}"
        if template_key not in self.templates:
            template_key = f"{use_case}_default"
            
        template = self.templates[template_key]
        return template.format(**kwargs)
```

### Model-Specific Optimizations

| Model | Prompt Style | Temperature | Max Tokens | Special Considerations |
|-------|--------------|-------------|------------|----------------------|
| **Mistral 7B** | Structured | 0.1 | 4000 | Responds well to explicit instructions |
| **Llama 3.1** | Conversational | 0.1 | 8000 | Benefits from system messages |
| **Phi-3** | Concise | 0.2 | 2000 | Prefers shorter, direct prompts |

## Performance Monitoring

### Metrics Tracking

```python
class LLMMetrics:
    """Tracks LLM performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'response_time': [],
            'token_count': [],
            'error_rate': 0,
            'throughput': 0
        }
    
    def record_request(
        self, 
        response_time: float,
        input_tokens: int,
        output_tokens: int,
        success: bool
    ):
        """Record metrics for a single request."""
        self.metrics['response_time'].append(response_time)
        self.metrics['token_count'].append(input_tokens + output_tokens)
        
        if not success:
            self.metrics['error_rate'] += 1
```

### Benchmarking Framework

- **Response Quality**: BLEU scores, human evaluation
- **Response Time**: P50, P95, P99 latencies
- **Resource Usage**: CPU, RAM, GPU utilization
- **Throughput**: Queries per second under load

## Resource Management

### Memory Optimization

```python
class ModelResourceManager:
    """Manages model loading and memory usage."""
    
    def __init__(self):
        self.loaded_models = {}
        self.max_memory_usage = 0.8  # 80% of available memory
    
    def load_model(self, provider_type: str, model_name: str):
        """Load model with memory management."""
        
        # Check available memory
        available_memory = self._get_available_memory()
        model_memory_req = self._estimate_model_memory(model_name)
        
        if model_memory_req > available_memory:
            self._unload_least_used_model()
        
        # Load the model
        provider = self._create_provider(provider_type, model_name)
        self.loaded_models[model_name] = provider
        
        return provider
```

### GPU Utilization

- **Model Placement**: Automatic GPU/CPU selection
- **Batch Processing**: Group requests for efficiency
- **Memory Pooling**: Reuse allocated memory blocks
- **Dynamic Scaling**: Scale based on load

## Success Criteria

### Functional Requirements
- [ ] Multiple LLM providers working seamlessly
- [ ] Model switching without service downtime
- [ ] Consistent interface across all providers
- [ ] Automatic failover between providers
- [ ] Configuration-driven model selection

### Performance Requirements
- [ ] Response time within 3 seconds for typical queries
- [ ] Support for multiple concurrent model instances
- [ ] Memory usage optimized for target hardware
- [ ] GPU utilization >70% when available

### Quality Requirements
- [ ] Prompt templates optimized for each model
- [ ] A/B testing shows performance improvements
- [ ] Benchmark suite validates model performance
- [ ] Error handling prevents system crashes

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model Performance Degradation** | High | Multiple models, benchmarking, fallback options |
| **Resource Exhaustion** | Medium | Memory management, model unloading, monitoring |
| **Provider API Changes** | Medium | Abstract interfaces, version pinning |
| **License Compliance** | High | Legal review, open-source alternatives |

## Timeline & Priority

**Timeline**: 2-3 weeks | **Priority**: High | **Dependencies**: Goal 1

### Week 1: Foundation
- Provider interface design
- Ollama integration
- Basic prompt system

### Week 2: Expansion
- Additional provider implementations
- Advanced prompt engineering
- Performance monitoring

### Week 3: Optimization
- Resource management
- Benchmarking suite
- Production hardening

## Next Steps

Upon completion of Goal 3:
1. Proceed to [Goal 4: Natural Language to SQL](goal-4.md)
2. Begin model performance optimization
3. Establish model update procedures

## Related Documentation

- [Goal 1: Technical Foundation](goal-1.md)
- [Goal 2: Interactive Q&A Interface](goal-2.md)
- [Goal 4: Database Q&A](goal-4.md) 