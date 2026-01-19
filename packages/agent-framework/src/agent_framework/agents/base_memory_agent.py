"""
Memory-aware agent base class using LangGraph's native memory system.

This module provides a base class for agents that can remember and recall information
across different conversation threads within the same engagement.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import uuid
import logging

from langgraph.prebuilt import create_react_agent
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.tools import tool, BaseTool
from langchain_core.language_models import BaseChatModel

from agent_framework.memory.long_term import EngagementMemoryStore, MemoryTypes

logger = logging.getLogger(__name__)


class MemoryAwareAgent(ABC):
    """
    Base class for agents with long-term memory capabilities.

    This class integrates LangGraph's memory system to provide agents with:
    - Short-term memory: Thread checkpoints via PostgresSaver
    - Long-term memory: Cross-thread semantic search via PostgresStore

    Example:
        class MyAgent(MemoryAwareAgent):
            def get_tools(self) -> List[BaseTool]:
                return [my_custom_tool]

            def get_system_prompt(self) -> str:
                return "You are a helpful assistant..."

        agent = MyAgent(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str),
            engagement_id="eng_123",
            agent_id="my_agent"
        )
        result = await agent.run("Analyze the stakeholders", thread_id="thread_1")
    """

    def __init__(
        self,
        llm: BaseChatModel,
        checkpointer: PostgresSaver,
        store: PostgresStore,
        engagement_id: str,
        agent_id: str,
    ):
        """
        Initialize the memory-aware agent.

        Args:
            llm: The language model to use
            checkpointer: PostgresSaver for short-term thread checkpoints
            store: PostgresStore for long-term cross-thread memory
            engagement_id: The engagement this agent operates within
            agent_id: Unique identifier for this agent instance
        """
        self.llm = llm
        self.checkpointer = checkpointer
        self.store = store
        self.engagement_id = engagement_id
        self.agent_id = agent_id

        # Create memory tools
        self.memory_tools = self._create_memory_tools()

        # Build the agent with memory capabilities
        self.agent = create_react_agent(
            model=llm,
            tools=self.get_tools() + self.memory_tools,
            checkpointer=checkpointer,
            store=store,
            state_modifier=self._get_state_modifier(),
        )

    def _create_memory_tools(self) -> List[BaseTool]:
        """
        Create tools for memory operations (remember and recall).

        Returns:
            List of memory-related tools
        """
        store = self.store
        engagement_id = self.engagement_id
        agent_id = self.agent_id

        @tool
        async def remember(
            content: str,
            memory_type: str = "general"
        ) -> str:
            """
            Store important information for future reference.

            Use this to save key insights, decisions, stakeholder information,
            or any context that should persist across conversations.

            Args:
                content: The information to remember
                memory_type: Category of memory. Valid types:
                    - stakeholder: Information about people and roles
                    - requirement: Business or technical requirements
                    - decision: Decisions made during the engagement
                    - insight: Key insights or observations
                    - artifact: References to created artifacts
                    - feedback: User or stakeholder feedback
                    - general: Other important information

            Returns:
                Confirmation message with the stored memory key
            """
            namespace = ("engagements", engagement_id, memory_type)
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": content,
                        "agent_id": agent_id,
                        "search_text": content,
                    }
                )
                logger.info(f"Agent {agent_id} stored memory: type={memory_type}, key={key}")
                return f"Stored memory [{memory_type}]: {key}"
            except Exception as e:
                logger.error(f"Error storing memory: {e}")
                return f"Failed to store memory: {str(e)}"

        @tool
        async def recall(
            query: str,
            memory_type: Optional[str] = None,
            limit: int = 5
        ) -> str:
            """
            Search past memories for relevant information.

            Use this to retrieve previously stored context about stakeholders,
            requirements, decisions, or any other relevant information.

            Args:
                query: Natural language description of what to search for
                memory_type: Optional category to search within. If not specified,
                    searches all memory types. Valid types:
                    - stakeholder, requirement, decision, insight,
                    - artifact, feedback, general
                limit: Maximum number of results to return (default: 5)

            Returns:
                Formatted list of relevant memories or "No relevant memories found"
            """
            if memory_type:
                namespace = ("engagements", engagement_id, memory_type)
            else:
                namespace = ("engagements", engagement_id)

            try:
                results = await store.asearch(namespace, query=query, limit=limit)

                if not results:
                    return "No relevant memories found."

                formatted_results = []
                for i, r in enumerate(results, 1):
                    content = r.value.get("content", str(r.value))
                    score = getattr(r, "score", None)
                    score_str = f" (relevance: {score:.2f})" if score else ""
                    formatted_results.append(f"{i}. {content}{score_str}")

                return "\n".join(formatted_results)
            except Exception as e:
                logger.error(f"Error recalling memories: {e}")
                return f"Failed to search memories: {str(e)}"

        return [remember, recall]

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """
        Get agent-specific tools.

        Override in subclasses to provide custom tools for the agent.
        Memory tools (remember, recall) are automatically added.

        Returns:
            List of agent-specific tools
        """
        pass

    def get_system_prompt(self) -> Optional[str]:
        """
        Get the system prompt for the agent.

        Override in subclasses to customize the agent's behavior.

        Returns:
            System prompt string or None for default behavior
        """
        return None

    def _get_state_modifier(self) -> Optional[str]:
        """
        Get the state modifier (system prompt) for the agent.

        Returns:
            The system prompt if defined, otherwise None
        """
        prompt = self.get_system_prompt()
        if prompt:
            return f"""{prompt}

You have access to memory tools to store and retrieve information:
- Use 'remember' to store important information for future reference
- Use 'recall' to search for relevant past information

Current engagement: {self.engagement_id}
"""
        return None

    async def run(
        self,
        input_message: str,
        thread_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the agent with memory context.

        Args:
            input_message: The user's input message
            thread_id: Unique identifier for this conversation thread
            additional_context: Optional additional context to include

        Returns:
            The agent's response including messages and any tool outputs
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "engagement_id": self.engagement_id,
            }
        }

        messages = [{"role": "user", "content": input_message}]

        if additional_context:
            context_str = "\n".join(
                f"{k}: {v}" for k, v in additional_context.items()
            )
            messages[0]["content"] = f"Context:\n{context_str}\n\nRequest: {input_message}"

        try:
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=config,
            )

            logger.info(
                f"Agent {self.agent_id} completed run for thread {thread_id}"
            )

            return result
        except Exception as e:
            logger.error(f"Agent {self.agent_id} error: {e}")
            raise

    async def run_stream(
        self,
        input_message: str,
        thread_id: str,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        Execute the agent with streaming output.

        Args:
            input_message: The user's input message
            thread_id: Unique identifier for this conversation thread
            additional_context: Optional additional context to include

        Yields:
            Streaming events from the agent execution
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "engagement_id": self.engagement_id,
            }
        }

        messages = [{"role": "user", "content": input_message}]

        if additional_context:
            context_str = "\n".join(
                f"{k}: {v}" for k, v in additional_context.items()
            )
            messages[0]["content"] = f"Context:\n{context_str}\n\nRequest: {input_message}"

        async for event in self.agent.astream(
            {"messages": messages},
            config=config,
        ):
            yield event

    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a specific thread.

        Args:
            thread_id: The thread to get history for

        Returns:
            List of messages in the thread
        """
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state = self.checkpointer.get(config)
            if state and "messages" in state.values:
                return state.values["messages"]
            return []
        except Exception as e:
            logger.error(f"Error getting thread history: {e}")
            return []


class SimpleMemoryAwareAgent(MemoryAwareAgent):
    """
    A simple memory-aware agent with no custom tools.

    Useful for general-purpose tasks that only need memory capabilities.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        checkpointer: PostgresSaver,
        store: PostgresStore,
        engagement_id: str,
        agent_id: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
    ):
        """
        Initialize a simple memory-aware agent.

        Args:
            llm: The language model to use
            checkpointer: PostgresSaver for short-term thread checkpoints
            store: PostgresStore for long-term cross-thread memory
            engagement_id: The engagement this agent operates within
            agent_id: Unique identifier for this agent instance
            system_prompt: Optional custom system prompt
            tools: Optional list of additional tools
        """
        self._system_prompt = system_prompt
        self._tools = tools or []
        super().__init__(llm, checkpointer, store, engagement_id, agent_id)

    def get_tools(self) -> List[BaseTool]:
        """Return the configured tools."""
        return self._tools

    def get_system_prompt(self) -> Optional[str]:
        """Return the configured system prompt."""
        return self._system_prompt
