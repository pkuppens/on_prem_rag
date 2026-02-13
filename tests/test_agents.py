# tests/test_agents.py
"""
Tests for the enhanced CrewAI agent framework.

Tests cover:
- Base agent configuration and creation
- LLM selector functionality
- Agent-specific LLM routing
- Memory hooks interface
"""

import os
from unittest.mock import MagicMock, patch


from backend.rag_pipeline.agents.base_agent import (
    AgentConfig,
    AgentMetrics,
    MemoryHooks,
)
from backend.rag_pipeline.agents.llm_selector import (
    DEFAULT_AGENT_LLM_MAPPING,
    AgentLLMSelector,
    LLMConfig,
    get_llm_for_agent,
    get_llm_selector,
)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_values(self):
        """As a developer I want default values for AgentConfig, so I can create configs easily."""
        config = AgentConfig(
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory",
        )

        assert config.role == "Test Role"
        assert config.goal == "Test Goal"
        assert config.backstory == "Test Backstory"
        assert config.llm_provider == "ollama"
        assert config.llm_model == "llama3.2:3b"
        assert config.llm_temperature == 0.7
        assert config.allow_delegation is False
        assert config.verbose is True
        assert config.max_iterations == 25
        assert config.tools == []
        assert config.cache is True

    def test_custom_values(self):
        """As a developer I want to override default values, so I can customize agents."""
        config = AgentConfig(
            role="Custom Role",
            goal="Custom Goal",
            backstory="Custom Backstory",
            llm_provider="openai",
            llm_model="gpt-4o",
            llm_temperature=0.5,
            allow_delegation=True,
            verbose=False,
            max_iterations=50,
        )

        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4o"
        assert config.llm_temperature == 0.5
        assert config.allow_delegation is True
        assert config.verbose is False
        assert config.max_iterations == 50


class TestAgentMetrics:
    """Tests for AgentMetrics dataclass."""

    def test_default_values(self):
        """As a developer I want metrics initialized to zero, so I can track agent activity."""
        metrics = AgentMetrics()

        assert metrics.llm_calls == 0
        assert metrics.total_tokens == 0
        assert metrics.execution_time_seconds == 0.0
        assert metrics.errors == 0
        assert metrics.cache_hits == 0

    def test_metrics_can_be_updated(self):
        """As a developer I want to update metrics, so I can track agent activity."""
        metrics = AgentMetrics()
        metrics.llm_calls = 5
        metrics.errors = 1

        assert metrics.llm_calls == 5
        assert metrics.errors == 1


class TestMemoryHooks:
    """Tests for MemoryHooks interface."""

    def test_initialization(self):
        """As a developer I want MemoryHooks to initialize with agent name."""
        hooks = MemoryHooks("TestAgent")
        assert hooks.agent_name == "TestAgent"
        assert hooks._short_term_cache == {}

    def test_short_term_memory_store_retrieve(self):
        """As a developer I want to store and retrieve short-term memory."""
        hooks = MemoryHooks("TestAgent")

        hooks.store_short_term("key1", "value1")
        hooks.store_short_term("key2", {"nested": "data"})

        assert hooks.retrieve_short_term("key1") == "value1"
        assert hooks.retrieve_short_term("key2") == {"nested": "data"}
        assert hooks.retrieve_short_term("nonexistent") is None

    def test_clear_short_term_memory(self):
        """As a developer I want to clear short-term memory."""
        hooks = MemoryHooks("TestAgent")
        hooks.store_short_term("key1", "value1")
        hooks.store_short_term("key2", "value2")

        hooks.clear_short_term()

        assert hooks.retrieve_short_term("key1") is None
        assert hooks.retrieve_short_term("key2") is None

    def test_task_lifecycle_hooks(self):
        """As a developer I want task lifecycle hooks, so I can track task execution."""
        hooks = MemoryHooks("TestAgent")

        # These should not raise exceptions
        hooks.on_task_start("Test task description")
        hooks.on_task_complete("Test task description", {"result": "success"})
        hooks.on_error(ValueError("Test error"), "test_context")


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_minimal_config(self):
        """As a developer I want to create LLMConfig with minimal parameters."""
        config = LLMConfig(provider="ollama", model="llama3.2:3b")

        assert config.provider == "ollama"
        assert config.model == "llama3.2:3b"
        assert config.temperature == 0.7
        assert config.base_url is None
        assert config.api_key is None

    def test_full_config(self):
        """As a developer I want to create LLMConfig with all parameters."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.5,
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            max_tokens=4000,
            top_p=0.9,
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.base_url == "https://api.openai.com/v1"
        assert config.api_key == "test-key"
        assert config.max_tokens == 4000
        assert config.top_p == 0.9


class TestAgentLLMSelector:
    """Tests for AgentLLMSelector class."""

    def test_default_mapping_exists(self):
        """As a developer I want default agent-LLM mappings for all agents."""
        assert "PreprocessingAgent" in DEFAULT_AGENT_LLM_MAPPING
        assert "ClinicalExtractorAgent" in DEFAULT_AGENT_LLM_MAPPING
        assert "LanguageAssessorAgent" in DEFAULT_AGENT_LLM_MAPPING
        assert "SummarizationAgent" in DEFAULT_AGENT_LLM_MAPPING
        assert "QualityControlAgent" in DEFAULT_AGENT_LLM_MAPPING

    def test_selector_initialization(self):
        """As a developer I want to initialize selector with default mappings."""
        selector = AgentLLMSelector()

        # Should have all default mappings
        mappings = selector.get_all_mappings()
        assert "PreprocessingAgent" in mappings
        assert "ClinicalExtractorAgent" in mappings

    def test_selector_custom_mapping(self):
        """As a developer I want to override default mappings with custom configs."""
        custom_config = LLMConfig(provider="openai", model="gpt-4o", temperature=0.3)
        custom_mapping = {"PreprocessingAgent": custom_config}

        selector = AgentLLMSelector(custom_mapping=custom_mapping)

        config = selector.get_config("PreprocessingAgent")
        assert config.provider == "openai"
        assert config.model == "gpt-4o"

    def test_selector_default_config_fallback(self):
        """As a developer I want fallback config for unknown agents."""
        selector = AgentLLMSelector()

        config = selector.get_config("UnknownAgent")
        # Should return the default fallback config
        assert config.provider == "ollama"
        assert config.model == "llama3.2:3b"

    def test_selector_update_mapping(self):
        """As a developer I want to update mappings at runtime."""
        selector = AgentLLMSelector()
        new_config = LLMConfig(provider="anthropic", model="claude-3-opus")

        selector.update_mapping("PreprocessingAgent", new_config)

        config = selector.get_config("PreprocessingAgent")
        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus"

    def test_selector_cache_clearing(self):
        """As a developer I want to clear LLM cache when needed."""
        selector = AgentLLMSelector()
        selector._llm_cache["test"] = MagicMock()

        selector.clear_cache()

        assert len(selector._llm_cache) == 0

    @patch.dict(
        os.environ,
        {
            # PreprocessingAgent.upper() = PREPROCESSINGAGENT, then _AGENT is appended
            "AGENT_LLM_PREPROCESSINGAGENT_AGENT_MODEL": "custom-model",
            "AGENT_LLM_PREPROCESSINGAGENT_AGENT_PROVIDER": "custom-provider",
        },
    )
    def test_selector_env_overrides(self):
        """As a developer I want environment variables to override configs."""
        selector = AgentLLMSelector()

        config = selector.get_config("PreprocessingAgent")
        assert config.model == "custom-model"
        assert config.provider == "custom-provider"


class TestGlobalLLMSelector:
    """Tests for global LLM selector singleton."""

    def test_get_llm_selector_singleton(self):
        """As a developer I want a singleton LLM selector instance."""
        selector1 = get_llm_selector()
        selector2 = get_llm_selector()

        # Should return the same instance
        assert selector1 is selector2

    @patch("backend.rag_pipeline.agents.llm_selector.AgentLLMSelector")
    def test_get_llm_for_agent(self, mock_selector_class):
        """As a developer I want a convenience function to get LLMs for agents."""
        mock_llm = MagicMock()
        mock_selector = MagicMock()
        mock_selector.create_llm.return_value = mock_llm
        mock_selector_class.return_value = mock_selector

        # Reset the global selector
        import backend.rag_pipeline.agents.llm_selector as llm_module

        llm_module._global_selector = mock_selector

        result = get_llm_for_agent("PreprocessingAgent")

        mock_selector.create_llm.assert_called_once_with("PreprocessingAgent")
        assert result is mock_llm


class TestAgentImports:
    """Tests for agent module imports."""

    def test_all_agents_importable(self):
        """As a developer I want all agents to be importable from the module."""
        from backend.rag_pipeline.agents import (
            AgentConfig,
            AgentLLMSelector,
            AgentMetrics,
            BaseRAGAgent,
            ClinicalExtractorAgent,
            LanguageAssessorAgent,
            LLMConfig,
            MemoryHooks,
            PreprocessingAgent,
            QualityControlAgent,
            SummarizationAgent,
            create_medical_crew,
            get_llm_for_agent,
            get_llm_selector,
        )

        # All imports should succeed
        assert PreprocessingAgent is not None
        assert LanguageAssessorAgent is not None
        assert ClinicalExtractorAgent is not None
        assert SummarizationAgent is not None
        assert QualityControlAgent is not None
        assert BaseRAGAgent is not None
        assert AgentConfig is not None
        assert AgentMetrics is not None
        assert MemoryHooks is not None
        assert AgentLLMSelector is not None
        assert LLMConfig is not None
        assert get_llm_for_agent is not None
        assert get_llm_selector is not None
        assert create_medical_crew is not None

    def test_orchestrator_importable(self):
        """As a developer I want orchestrator to be importable."""
        from backend.rag_pipeline.agents.orchestrator import (
            MedicalCrewOrchestrator,
            OrchestrationResult,
            ProcessType,
            TaskDefinition,
            create_medical_orchestrator,
        )

        assert MedicalCrewOrchestrator is not None
        assert OrchestrationResult is not None
        assert ProcessType is not None
        assert TaskDefinition is not None
        assert create_medical_orchestrator is not None


class TestProcessType:
    """Tests for ProcessType enum."""

    def test_process_types(self):
        """As a developer I want clear process type definitions."""
        from backend.rag_pipeline.agents.orchestrator import ProcessType

        assert ProcessType.SEQUENTIAL.value == "sequential"
        assert ProcessType.HIERARCHICAL.value == "hierarchical"


class TestOrchestrationResult:
    """Tests for OrchestrationResult dataclass."""

    def test_success_result(self):
        """As a developer I want to create success results."""
        from backend.rag_pipeline.agents.orchestrator import OrchestrationResult

        result = OrchestrationResult(
            success=True,
            output="Test output",
            task_outputs=["task1", "task2"],
            metrics={"llm_calls": 5},
        )

        assert result.success is True
        assert result.output == "Test output"
        assert len(result.task_outputs) == 2
        assert result.metrics["llm_calls"] == 5
        assert result.errors == []

    def test_failure_result(self):
        """As a developer I want to create failure results."""
        from backend.rag_pipeline.agents.orchestrator import OrchestrationResult

        result = OrchestrationResult(
            success=False,
            output=None,
            errors=["Error 1", "Error 2"],
        )

        assert result.success is False
        assert result.output is None
        assert len(result.errors) == 2


class TestTaskDefinition:
    """Tests for TaskDefinition dataclass."""

    def test_task_definition(self):
        """As a developer I want to define tasks with dependencies."""
        from backend.rag_pipeline.agents.orchestrator import TaskDefinition

        task = TaskDefinition(
            description="Process medical text",
            expected_output="Processed text",
            agent_name="preprocessor",
            context_from=["previous_task"],
        )

        assert task.description == "Process medical text"
        assert task.expected_output == "Processed text"
        assert task.agent_name == "preprocessor"
        assert task.context_from == ["previous_task"]

    def test_task_definition_without_context(self):
        """As a developer I want to define tasks without dependencies."""
        from backend.rag_pipeline.agents.orchestrator import TaskDefinition

        task = TaskDefinition(
            description="Process medical text",
            expected_output="Processed text",
            agent_name="preprocessor",
        )

        assert task.context_from is None
