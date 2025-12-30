"""Agent callback handlers for CrewAI integration with Chainlit UI."""

import logging
from typing import Any

import chainlit as cl

from frontend.chat.utils.session import SessionManager, UserRole

logger = logging.getLogger(__name__)


class AgentCallbackHandler:
    """Handles callbacks from CrewAI agents to display in Chainlit UI.

    This handler provides real-time visibility into agent operations:
    - Agent thinking/reasoning steps
    - Tool usage and results
    - Task progress and completion
    """

    def __init__(self):
        self._orchestrator = None
        self._memory_manager = None
        self._guardrails = None

    def set_orchestrator(self, orchestrator: Any) -> None:
        """Set the CrewAI orchestrator instance."""
        self._orchestrator = orchestrator

    def set_memory_manager(self, memory_manager: Any) -> None:
        """Set the memory manager instance."""
        self._memory_manager = memory_manager

    def set_guardrails(self, guardrails: Any) -> None:
        """Set the guardrails instance."""
        self._guardrails = guardrails

    async def process_message(self, content: str, role: UserRole) -> None:
        """Process a message through the agent framework.

        Routes to the appropriate agent based on user role and displays
        agent steps in real-time.
        """
        # Create a parent step for the entire agent interaction
        async with cl.Step(name="Agent Processing", type="run") as parent_step:
            parent_step.input = content

            try:
                # Apply guardrails to input if available
                validated_input = await self._apply_input_guardrails(content, parent_step)
                if validated_input is None:
                    return

                # Route to appropriate agent
                if self._orchestrator:
                    result = await self._run_with_orchestrator(validated_input, role, parent_step)
                else:
                    result = await self._run_fallback(validated_input, role, parent_step)

                # Apply guardrails to output
                final_result = await self._apply_output_guardrails(result, parent_step)

                # Send final response
                await self._send_response(final_result)

            except Exception as e:
                logger.exception("Error processing message through agents")
                await self._handle_error(e, parent_step)

    async def _apply_input_guardrails(self, content: str, parent_step: cl.Step) -> str | None:
        """Apply input guardrails to validate the message."""
        if not self._guardrails:
            return content

        async with cl.Step(name="Input Validation", type="tool", parent_id=parent_step.id) as step:
            step.input = "Validating input against guardrails"
            try:
                # Call guardrails validation
                result = await self._guardrails.validate_input(content)
                if result.get("blocked"):
                    step.output = f"Input blocked: {result.get('reason', 'Policy violation')}"
                    await cl.Message(content="I cannot process this request due to content policy restrictions.").send()
                    return None
                step.output = "Input validated successfully"
                return result.get("sanitized_input", content)
            except Exception as e:
                step.output = f"Guardrails check failed: {e}"
                logger.warning(f"Guardrails check failed, proceeding with original input: {e}")
                return content

    async def _apply_output_guardrails(self, content: str, parent_step: cl.Step) -> str:
        """Apply output guardrails to filter the response."""
        if not self._guardrails:
            return content

        async with cl.Step(name="Output Filtering", type="tool", parent_id=parent_step.id) as step:
            step.input = "Filtering output against guardrails"
            try:
                result = await self._guardrails.filter_output(content)
                step.output = "Output filtered successfully"
                return result.get("filtered_output", content)
            except Exception as e:
                step.output = f"Output filtering failed: {e}"
                logger.warning(f"Output filtering failed: {e}")
                return content

    async def _run_with_orchestrator(self, content: str, role: UserRole, parent_step: cl.Step) -> str:
        """Run the query through the CrewAI orchestrator."""
        # Select agent based on role
        agent_name = self._get_agent_for_role(role)

        async with cl.Step(name=f"Agent: {agent_name}", type="llm", parent_id=parent_step.id) as agent_step:
            agent_step.input = content

            # Show agent thinking
            thinking_msg = await cl.Message(content="").send()

            try:
                # Get the appropriate agent
                agent_wrapper = self._orchestrator.get_agent(agent_name)
                # Our backend orchestrator returns `BaseRAGAgent` wrappers which expose a `.agent`
                # (the actual `crewai.Agent` instance expected by `crewai.Task`).
                agent = getattr(agent_wrapper, "agent", agent_wrapper)

                # Create and run the task
                from crewai import Task

                task = Task(description=content, agent=agent, expected_output="A helpful response to the user's query.")

                # Run the crew with callbacks
                result = await self._run_crew_with_callbacks(task, agent_step, thinking_msg)

                agent_step.output = result
                return result

            except Exception as e:
                agent_step.output = f"Error: {e}"
                raise

    def _get_agent_for_role(self, role: UserRole) -> str:
        """Get the appropriate agent name for the user role."""
        role_agent_map = {
            UserRole.GP: "clinical_extractor",  # GP gets clinical analysis
            # Backend `MedicalCrewOrchestrator` agent keys: preprocessor, language_assessor,
            # clinical_extractor, summarizer, quality_controller.
            UserRole.PATIENT: "summarizer",  # Patient gets summaries
            UserRole.ADMIN: "quality_controller",  # Admin gets the most complete oversight view
        }
        return role_agent_map.get(role, "summarizer")

    async def _run_crew_with_callbacks(self, task: Any, agent_step: cl.Step, thinking_msg: cl.Message) -> str:
        """Run a CrewAI task with UI callbacks for visibility."""
        from crewai import Crew

        # Create a minimal crew for this task
        crew = Crew(agents=[task.agent], tasks=[task], verbose=True)

        # Stream thinking updates
        thinking_text = "Thinking..."
        await thinking_msg.stream_token(thinking_text)

        # Execute the crew
        # Note: In a real implementation, we would use CrewAI's callback system
        # to stream updates in real-time
        result = crew.kickoff()

        # Clear thinking message and show we're done
        thinking_msg.content = ""
        await thinking_msg.update()

        return str(result)

    async def _run_fallback(self, content: str, role: UserRole, parent_step: cl.Step) -> str:
        """Fallback processing when orchestrator isn't available."""
        async with cl.Step(name="Fallback Processing", type="llm", parent_id=parent_step.id) as step:
            step.input = content

            # Role-specific context
            role_contexts = {
                UserRole.GP: "You are assisting a healthcare professional with clinical questions.",
                UserRole.PATIENT: "You are assisting a patient with health-related questions.",
                UserRole.ADMIN: "You are assisting an administrator with system queries.",
            }

            context = role_contexts.get(role, "You are a helpful assistant.")

            result = (
                f"[{context}]\n\n"
                f"I received your query: '{content}'\n\n"
                "The full agent framework is not currently connected. "
                "Please ensure the backend services are running and properly configured.\n\n"
                "To start the services:\n"
                "1. Start the RAG backend: `uv run start-backend`\n"
                "2. Start the auth service: `uv run start-auth`"
            )

            step.output = result
            return result

    async def _send_response(self, content: str) -> None:
        """Send the final response to the user."""
        response = cl.Message(content="")
        await response.send()

        # Stream the response for better UX
        for char in content:
            await response.stream_token(char)

        await response.update()

        # Add to conversation history
        SessionManager.add_to_conversation("assistant", content)

    async def _handle_error(self, error: Exception, parent_step: cl.Step) -> None:
        """Handle errors during agent processing."""
        error_msg = f"An error occurred while processing your request: {type(error).__name__}"

        async with cl.Step(name="Error", type="tool", parent_id=parent_step.id) as step:
            step.output = str(error)

        await cl.Message(content=f"{error_msg}\n\nPlease try again or contact support if the issue persists.").send()

    async def on_agent_start(self, agent_name: str, task_description: str) -> cl.Step:
        """Callback when an agent starts a task."""
        step = cl.Step(name=f"Agent: {agent_name}", type="llm")
        step.input = task_description
        await step.send()
        return step

    async def on_agent_thinking(self, step: cl.Step, thought: str) -> None:
        """Callback when an agent is thinking/reasoning."""
        await step.stream_token(f"\n**Thinking:** {thought}")

    async def on_tool_start(self, tool_name: str, tool_input: str, parent_step: cl.Step) -> cl.Step:
        """Callback when a tool is invoked."""
        step = cl.Step(name=f"Tool: {tool_name}", type="tool", parent_id=parent_step.id)
        step.input = tool_input
        await step.send()
        return step

    async def on_tool_end(self, step: cl.Step, tool_output: str) -> None:
        """Callback when a tool completes."""
        step.output = tool_output
        await step.update()

    async def on_agent_end(self, step: cl.Step, final_answer: str) -> None:
        """Callback when an agent completes its task."""
        step.output = final_answer
        await step.update()


# Global agent callback handler instance
_agent_handler: AgentCallbackHandler | None = None


def get_agent_handler() -> AgentCallbackHandler:
    """Get the global agent callback handler instance."""
    global _agent_handler
    if _agent_handler is None:
        _agent_handler = AgentCallbackHandler()
    return _agent_handler
