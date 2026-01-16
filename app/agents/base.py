"""
Agent Base Classes and Strategy Pattern

This module defines the abstract base classes and strategy interfaces
for the AI SDLC agents. The Strategy Pattern allows switching between
standard and strict output modes based on quality requirements.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from app.utils.logger import logger


class AgentMode(str, Enum):
    """Agent execution modes"""
    STANDARD = "standard"
    STRICT = "strict"


class QualityMetrics(BaseModel):
    """Quality metrics for agent output evaluation"""
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall confidence in output")
    completeness_score: float = Field(ge=0.0, le=1.0, description="How complete the output is")
    items_count: int = Field(ge=0, description="Number of items produced")
    has_errors: bool = Field(default=False, description="Whether errors occurred")
    error_messages: List[str] = Field(default_factory=list)
    
    def passes_quality_gate(self, min_confidence: float = 0.7) -> bool:
        """Check if output passes quality gate"""
        return (
            self.confidence_score >= min_confidence and
            not self.has_errors and
            self.items_count > 0
        )


class ReasoningTrace(BaseModel):
    """Trace of AI reasoning steps"""
    steps: List[str] = Field(default_factory=list)
    rag_sources_used: List[str] = Field(default_factory=list)
    patterns_matched: List[str] = Field(default_factory=list)
    decisions_made: List[Dict[str, str]] = Field(default_factory=list)


class AgentOutput(BaseModel):
    """Base class for all agent outputs"""
    agent_name: str
    mode: AgentMode
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    quality_metrics: QualityMetrics
    reasoning_trace: ReasoningTrace = Field(default_factory=ReasoningTrace)
    raw_response: Optional[str] = None


T = TypeVar('T', bound=AgentOutput)


class AgentStrategy(ABC, Generic[T]):
    """
    Abstract strategy interface for agent execution modes.
    
    Implementations define how prompts are constructed and
    how responses are parsed for different quality levels.
    """
    
    @property
    @abstractmethod
    def mode(self) -> AgentMode:
        """Return the mode this strategy implements"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this strategy.
        
        Returns:
            System prompt string for the LLM
        """
        pass
    
    @abstractmethod
    def get_user_prompt(self, **kwargs) -> str:
        """
        Get the user prompt for this strategy.
        
        Args:
            **kwargs: Context-specific arguments
        
        Returns:
            User prompt string for the LLM
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response into structured data.
        
        Args:
            response: Raw LLM response string
        
        Returns:
            Parsed data dictionary
        """
        pass
    
    @abstractmethod
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> T:
        """
        Create the typed output from parsed data.
        
        Args:
            parsed_data: Parsed response data
            **kwargs: Additional context
        
        Returns:
            Typed agent output
        """
        pass
    
    def get_output_schema(self) -> Optional[Type[BaseModel]]:
        """
        Get the Pydantic schema for structured output (if using strict mode).
        
        Returns:
            Pydantic model class or None for standard mode
        """
        return None


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all SDLC agents.
    
    Implements the Strategy Pattern to allow switching between
    standard and strict execution modes based on quality requirements.
    
    Example usage:
        agent = RequirementAgent(strategy=StandardRequirementStrategy())
        result = await agent.execute(ticket_data)
        
        if not result.quality_metrics.passes_quality_gate():
            agent.set_strategy(StrictRequirementStrategy())
            result = await agent.execute(ticket_data)
    """
    
    def __init__(
        self,
        strategy: AgentStrategy[T],
        llm=None,
        vectorstore=None
    ):
        """
        Initialize the agent with a strategy.
        
        Args:
            strategy: The execution strategy to use
            llm: Optional LLM instance
            vectorstore: Optional vector store for RAG
        """
        self._strategy = strategy
        self.llm = llm
        self.vectorstore = vectorstore
        self._execution_count = 0
        self._retry_count = 0
        logger.info(f"Initialized {self.name} with {strategy.mode.value} strategy")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent name"""
        pass
    
    @property
    def strategy(self) -> AgentStrategy[T]:
        """Get the current strategy"""
        return self._strategy
    
    def set_strategy(self, strategy: AgentStrategy[T]) -> None:
        """
        Switch to a different strategy.
        
        Args:
            strategy: New strategy to use
        """
        old_mode = self._strategy.mode
        self._strategy = strategy
        logger.info(f"{self.name}: Switched strategy from {old_mode.value} to {strategy.mode.value}")
    
    async def execute(self, **kwargs) -> T:
        """
        Execute the agent with the current strategy.
        
        Args:
            **kwargs: Agent-specific arguments
        
        Returns:
            Typed agent output
        """
        self._execution_count += 1
        logger.info(f"{self.name}: Executing with {self._strategy.mode.value} strategy (execution #{self._execution_count})")
        
        try:
            # Get LLM
            llm = await self._get_llm()
            
            # Build prompts using strategy
            system_prompt = self._strategy.get_system_prompt()
            user_prompt = self._strategy.get_user_prompt(**kwargs)
            
            # Execute LLM call
            response = await self._call_llm(llm, system_prompt, user_prompt)
            
            # Parse response using strategy
            parsed_data = self._strategy.parse_response(response)
            
            # Create typed output
            output = self._strategy.create_output(parsed_data, **kwargs)
            output.raw_response = response
            
            logger.info(f"{self.name}: Completed with confidence {output.quality_metrics.confidence_score:.2f}")
            return output
            
        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {e}")
            return self._create_error_output(str(e), **kwargs)
    
    async def execute_with_retry(
        self,
        strict_strategy: AgentStrategy[T],
        min_confidence: float = 0.7,
        **kwargs
    ) -> T:
        """
        Execute with automatic retry using strict strategy if quality is low.
        
        Args:
            strict_strategy: Strategy to use for retry
            min_confidence: Minimum confidence threshold
            **kwargs: Agent-specific arguments
        
        Returns:
            Typed agent output (from either attempt)
        """
        # First attempt with current strategy
        result = await self.execute(**kwargs)
        
        # Check quality gate
        if result.quality_metrics.passes_quality_gate(min_confidence):
            return result
        
        # Retry with strict strategy
        logger.info(f"{self.name}: Quality gate failed (confidence={result.quality_metrics.confidence_score:.2f}), retrying with strict mode")
        self._retry_count += 1
        
        original_strategy = self._strategy
        self.set_strategy(strict_strategy)
        
        try:
            retry_result = await self.execute(**kwargs)
            retry_result.reasoning_trace.decisions_made.append({
                "decision": "retry_with_strict",
                "reason": f"Initial confidence {result.quality_metrics.confidence_score:.2f} < {min_confidence}"
            })
            return retry_result
        finally:
            # Restore original strategy
            self.set_strategy(original_strategy)
    
    async def _get_llm(self):
        """Get or create the LLM instance"""
        if self.llm:
            return self.llm
        
        from langchain_openai import ChatOpenAI
        from app.config import get_settings
        
        settings = get_settings()
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3
        )
    
    async def _call_llm(self, llm, system_prompt: str, user_prompt: str) -> str:
        """Execute the LLM call"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await llm.ainvoke(messages)
        return response.content.strip()
    
    @abstractmethod
    def _create_error_output(self, error: str, **kwargs) -> T:
        """
        Create an error output when execution fails.
        
        Args:
            error: Error message
            **kwargs: Original arguments
        
        Returns:
            Error output with quality metrics indicating failure
        """
        pass
    
    async def fetch_rag_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch relevant context from vector store.
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of relevant documents
        """
        if not self.vectorstore:
            return []
        
        # TODO: Implement actual RAG retrieval
        return []
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for this agent"""
        return {
            "agent_name": self.name,
            "current_mode": self._strategy.mode.value,
            "execution_count": self._execution_count,
            "retry_count": self._retry_count
        }
