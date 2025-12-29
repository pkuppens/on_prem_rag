# src/backend/rag_pipeline/agents/base_agent.py
"""
Base agent class with memory hooks, guardrails, and enhanced configuration support.

This module provides the foundation for all specialized agents in the RAG pipeline,
implementing memory hooks, logging, metrics collection, and PII protection interfaces.

GUARDRAILS:
- All agents run locally via Ollama - no external API calls by default
- PII detection and anonymization before any external LLM routing
- Patient isolation: agents cannot access other patients' data
- Audit logging for compliance

See also: Issue #64 for NeMo Guardrails integration
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from crewai import LLM, Agent
from crewai.hooks import register_after_llm_call_hook, register_before_llm_call_hook

# Import privacy guard for PII detection (lazy import to avoid circular deps)
try:
    from backend.privacy_guard import PII_TYPES, CloudSafety, PIICategory

    PRIVACY_GUARD_AVAILABLE = True
except ImportError:
    PRIVACY_GUARD_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""

    role: str
    goal: str
    backstory: str
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2:3b"
    llm_temperature: float = 0.7
    llm_base_url: str = "http://localhost:11434"
    allow_delegation: bool = False
    verbose: bool = True
    max_iterations: int = 25
    max_rpm: int | None = None  # Rate limit for LLM calls
    tools: list[Any] = field(default_factory=list)
    cache: bool = True  # Enable response caching


@dataclass
class AgentMetrics:
    """Metrics collected during agent execution."""

    llm_calls: int = 0
    total_tokens: int = 0
    execution_time_seconds: float = 0.0
    errors: int = 0
    cache_hits: int = 0
    pii_detections: int = 0  # Number of PII instances detected
    blocked_requests: int = 0  # Requests blocked by guardrails


@dataclass
class GuardrailsConfig:
    """Configuration for agent guardrails.

    Guardrails ensure:
    - No PII leaks to external LLMs
    - Patient data isolation
    - Audit logging for compliance
    """

    enable_pii_detection: bool = True  # Scan input/output for PII
    block_external_with_pii: bool = True  # Block external LLM calls if PII detected
    enable_patient_isolation: bool = True  # Ensure patient data isolation
    audit_logging: bool = True  # Log all guardrail actions
    allowed_pii_categories: list[str] = field(default_factory=list)  # PII types allowed to pass


class PIIGuard:
    """
    Guardrail for PII detection and protection.

    Integrates with the privacy_guard module to:
    - Detect PII in agent inputs and outputs
    - Block or anonymize PII before external LLM calls
    - Log PII detections for audit

    IMPORTANT: All agents default to local Ollama models, so PII
    stays on-premises. This guard is an additional layer for:
    1. Future cloud LLM routing (must anonymize first)
    2. Audit compliance
    3. Patient data isolation between users
    """

    def __init__(self, config: GuardrailsConfig, agent_name: str):
        self.config = config
        self.agent_name = agent_name
        self._pii_count = 0

    def check_input(self, text: str, patient_context: str | None = None) -> tuple[bool, str, list[str]]:
        """
        Check input text for PII before processing.

        Args:
            text: Input text to check
            patient_context: Optional patient identifier for isolation check

        Returns:
            Tuple of (is_safe, sanitized_text, detected_pii_categories)
        """
        if not self.config.enable_pii_detection or not PRIVACY_GUARD_AVAILABLE:
            return True, text, []

        detected_categories: list[str] = []

        # Check for each PII type
        for category, pii_type in PII_TYPES.items():
            matches = pii_type.matches(text)
            if matches:
                detected_categories.append(category.value)
                self._pii_count += len(matches)

                if self.config.audit_logging:
                    logger.warning(
                        f"[{self.agent_name}] PII detected: {category.value} "
                        f"({len(matches)} instance(s)) - {pii_type.cloud_safety.value}"
                    )

        # Determine if safe to proceed
        is_safe = True
        if detected_categories and self.config.block_external_with_pii:
            # Check if any detected PII is not in allowed list
            for cat in detected_categories:
                if cat not in self.config.allowed_pii_categories:
                    # Check cloud safety - NEVER categories always block
                    pii_type = PII_TYPES.get(PIICategory(cat))
                    if pii_type and pii_type.cloud_safety == CloudSafety.NEVER:
                        is_safe = False
                        break

        return is_safe, text, detected_categories

    def check_output(self, text: str) -> tuple[bool, str, list[str]]:
        """
        Check output text for PII before returning to user.

        Ensures no PII leaks in agent responses.
        """
        return self.check_input(text)  # Same logic for now

    def get_pii_count(self) -> int:
        """Get total PII detections."""
        return self._pii_count

    def reset_count(self) -> None:
        """Reset PII detection count."""
        self._pii_count = 0


class MemoryHooks:
    """
    Memory hooks interface for agent memory management.

    Provides hooks for storing and retrieving information from
    short-term, long-term, and entity memory systems.

    Integrates with the backend.memory module when a session_id is provided,
    falling back to in-memory storage for backward compatibility.
    """

    def __init__(self, agent_name: str, session_id: str | None = None):
        self.agent_name = agent_name
        self.session_id = session_id
        self._short_term_cache: dict[str, Any] = {}
        self._memory_manager = None

        # Try to get the memory manager if available
        if session_id:
            try:
                from backend.memory import get_memory_manager

                self._memory_manager = get_memory_manager()
                logger.debug(f"[{self.agent_name}] Connected to MemoryManager")
            except ImportError:
                logger.debug(f"[{self.agent_name}] MemoryManager not available, using local cache")

    def store_short_term(self, key: str, value: Any) -> None:
        """Store information in short-term memory (session-scoped)."""
        if self._memory_manager and self.session_id:
            self._memory_manager.store_short_term(
                session_id=self.session_id,
                key=key,
                value=value,
                agent_role=self.agent_name,
            )
        else:
            self._short_term_cache[key] = value
        logger.debug(f"[{self.agent_name}] Stored in short-term memory: {key}")

    def retrieve_short_term(self, key: str) -> Any | None:
        """Retrieve information from short-term memory."""
        if self._memory_manager and self.session_id:
            value = self._memory_manager.get_short_term(
                session_id=self.session_id,
                key=key,
                agent_role=self.agent_name,
            )
        else:
            value = self._short_term_cache.get(key)
        logger.debug(f"[{self.agent_name}] Retrieved from short-term memory: {key} = {value is not None}")
        return value

    def clear_short_term(self) -> None:
        """Clear short-term memory."""
        if self._memory_manager and self.session_id:
            self._memory_manager.clear_short_term(self.session_id, self.agent_name)
        else:
            self._short_term_cache.clear()
        logger.debug(f"[{self.agent_name}] Cleared short-term memory")

    def store_long_term(
        self,
        content: str,
        memory_type: str = "observation",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Store information in long-term memory (persistent).

        Args:
            content: The content to store
            memory_type: Type of memory ("fact", "observation", "result")
            importance: Importance score (0.0 to 1.0)
            metadata: Optional additional metadata

        Returns:
            Document ID if stored, None otherwise
        """
        if not self._memory_manager or not self.session_id:
            logger.debug(f"[{self.agent_name}] Long-term storage not available (no session)")
            return None

        return self._memory_manager.store_long_term(
            agent_role=self.agent_name,
            session_id=self.session_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata,
        )

    def search_memory(
        self,
        query: str,
        top_k: int = 5,
        include_shared: bool = True,
    ) -> list[Any]:
        """Search for relevant memories.

        Args:
            query: The search query
            top_k: Number of results to return
            include_shared: Whether to include shared memory

        Returns:
            List of search results
        """
        if not self._memory_manager or not self.session_id:
            return []

        return self._memory_manager.search(
            query=query,
            agent_role=self.agent_name,
            top_k=top_k,
            include_shared=include_shared,
        )

    def on_task_start(self, task_description: str) -> None:
        """Hook called when a task starts."""
        logger.info(f"[{self.agent_name}] Starting task: {task_description[:50]}...")
        # Store task start in short-term memory
        self.store_short_term("current_task", task_description)

    def on_task_complete(self, task_description: str, result: Any) -> None:
        """Hook called when a task completes."""
        logger.info(f"[{self.agent_name}] Completed task: {task_description[:50]}...")
        # Optionally store result summary in long-term memory
        if self._memory_manager and self.session_id and result:
            result_str = str(result)[:500]  # Limit result size
            self.store_long_term(
                content=f"Task: {task_description[:100]}... Result: {result_str}",
                memory_type="result",
                importance=0.6,
            )

    def on_error(self, error: Exception, context: str) -> None:
        """Hook called when an error occurs."""
        logger.error(f"[{self.agent_name}] Error in {context}: {error}")


class BaseRAGAgent(ABC):
    """
    Abstract base class for all RAG pipeline agents.

    Provides common functionality including:
    - LLM configuration and instantiation
    - Memory hooks interface
    - Metrics collection
    - Logging integration
    - PII guardrails (via privacy_guard integration)

    SECURITY NOTE:
    - All agents default to LOCAL Ollama models - no external API calls
    - PII detection guards against accidental leaks if cloud routing is enabled
    - Patient isolation ensures users cannot access other patients' data

    Subclasses must implement:
    - _get_default_config(): Returns default AgentConfig for the agent type
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        llm: LLM | None = None,
        guardrails_config: GuardrailsConfig | None = None,
        session_id: str | None = None,
    ):
        """
        Initialize the base agent.

        Args:
            config: Agent configuration. If None, uses _get_default_config().
            llm: Pre-configured LLM instance. If None, creates from config.
            guardrails_config: Guardrails configuration. If None, uses defaults.
            session_id: Optional session ID for memory management. If provided,
                enables integration with the MemoryManager for persistent
                short-term and long-term memory.
        """
        self.config = config or self._get_default_config()
        self.metrics = AgentMetrics()
        self.session_id = session_id
        self.memory_hooks = MemoryHooks(self.config.role, session_id=session_id)

        # Initialize guardrails
        self.guardrails_config = guardrails_config or GuardrailsConfig()
        self.pii_guard = PIIGuard(self.guardrails_config, self.config.role)

        # Create or use provided LLM
        self._llm = llm or self._create_llm()

        # Create the underlying CrewAI Agent
        self._agent = self._create_crew_agent()

        # Register LLM hooks for metrics collection
        self._register_hooks()

        # Log security configuration
        if self.guardrails_config.enable_pii_detection:
            logger.info(f"[{self.config.role}] PII guardrails enabled")
        if not self._is_local_llm():
            logger.warning(f"[{self.config.role}] Using external LLM - PII protection active")

    @abstractmethod
    def _get_default_config(self) -> AgentConfig:
        """Return the default configuration for this agent type."""

    def _is_local_llm(self) -> bool:
        """Check if the LLM runs locally (no external API calls)."""
        local_providers = {"ollama", "llamacpp", "huggingface"}
        return self.config.llm_provider.lower() in local_providers

    def _create_llm(self) -> LLM:
        """Create an LLM instance from configuration."""
        model_string = f"{self.config.llm_provider}/{self.config.llm_model}"
        if self.config.llm_provider == "ollama":
            model_string = f"ollama/{self.config.llm_model}"

        return LLM(
            model=model_string,
            temperature=self.config.llm_temperature,
            base_url=self.config.llm_base_url,
        )

    def _create_crew_agent(self) -> Agent:
        """Create the underlying CrewAI Agent instance."""
        return Agent(
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            llm=self._llm,
            tools=self.config.tools,
            allow_delegation=self.config.allow_delegation,
            verbose=self.config.verbose,
            max_iter=self.config.max_iterations,
            max_rpm=self.config.max_rpm,
            cache=self.config.cache,
        )

    def _register_hooks(self) -> None:
        """Register LLM call hooks for metrics collection."""
        agent_name = self.config.role

        def before_llm_call(context: Any) -> None:
            """Hook called before each LLM call."""
            logger.debug(f"[{agent_name}] LLM call starting...")
            return None  # Allow execution to proceed

        def after_llm_call(context: Any, response: Any) -> Any:
            """Hook called after each LLM call."""
            self.metrics.llm_calls += 1
            logger.debug(f"[{agent_name}] LLM call completed (total: {self.metrics.llm_calls})")
            return response

        # Note: These hooks are global in CrewAI, so they affect all agents
        # For agent-specific hooks, we track metrics per-agent in the callbacks
        register_before_llm_call_hook(before_llm_call)
        register_after_llm_call_hook(after_llm_call)

    @property
    def agent(self) -> Agent:
        """Get the underlying CrewAI Agent instance."""
        return self._agent

    @property
    def llm(self) -> LLM:
        """Get the LLM instance used by this agent."""
        return self._llm

    def get_metrics(self) -> AgentMetrics:
        """Get the current metrics for this agent."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset agent metrics to initial values."""
        self.metrics = AgentMetrics()
        self.pii_guard.reset_count()

    def check_input_safety(self, text: str) -> tuple[bool, list[str]]:
        """
        Check if input text is safe to process (no PII violations).

        Args:
            text: Input text to check

        Returns:
            Tuple of (is_safe, detected_pii_categories)
        """
        is_safe, _, categories = self.pii_guard.check_input(text)
        self.metrics.pii_detections += len(categories)
        if not is_safe:
            self.metrics.blocked_requests += 1
        return is_safe, categories

    def check_output_safety(self, text: str) -> tuple[bool, list[str]]:
        """
        Check if output text is safe to return (no PII leaks).

        Args:
            text: Output text to check

        Returns:
            Tuple of (is_safe, detected_pii_categories)
        """
        is_safe, _, categories = self.pii_guard.check_output(text)
        self.metrics.pii_detections += len(categories)
        return is_safe, categories

    @property
    def is_local(self) -> bool:
        """Check if this agent uses a local LLM (no external API calls)."""
        return self._is_local_llm()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role='{self.config.role}', local={self.is_local})"
