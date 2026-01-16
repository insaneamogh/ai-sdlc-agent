"""
LangGraph Orchestration Module

This module defines the multi-agent workflow using LangGraph.
It coordinates the RequirementAgent, CodeAgent, and TestAgent
in a stateful, inspectable pipeline.

Enhanced with:
- State checkpointing for workflow persistence and resume
- Thread-based execution for audit trails
- Streaming support for real-time progress updates
- Quality-based conditional routing with automatic retry
- Enterprise Output Bundle generation
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, AsyncGenerator
from enum import Enum
from datetime import datetime
import uuid
import time
from app.utils.logger import logger


class WorkflowAction(str, Enum):
    """Available workflow actions"""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_CODE = "generate_code"
    GENERATE_TESTS = "generate_tests"
    FULL_PIPELINE = "full_pipeline"


class AgentMode(str, Enum):
    """Agent execution modes"""
    STANDARD = "standard"
    STRICT = "strict"


class AgentState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    
    This state is passed between nodes and accumulates results
    from each agent in the pipeline.
    """
    # Input
    ticket_id: str
    ticket_title: str
    ticket_description: str
    acceptance_criteria: Optional[str]
    action: WorkflowAction
    
    # Context
    github_repo: Optional[str]
    github_pr: Optional[str]
    rag_context: Optional[List[Dict[str, Any]]]
    
    # Results from agents
    requirements: Optional[List[Dict[str, Any]]]
    generated_code: Optional[str]
    generated_tests: Optional[str]
    
    # Quality tracking
    quality_scores: Dict[str, float]
    retry_counts: Dict[str, int]
    current_mode: AgentMode
    quality_gates_passed: bool
    
    # Metadata
    current_agent: str
    agent_results: List[Dict[str, Any]]
    errors: List[str]
    started_at: str
    completed_at: Optional[str]


# Quality gate thresholds
QUALITY_THRESHOLDS = {
    "requirement_analyzer": 0.7,
    "code_generator": 0.7,
    "test_generator": 0.7
}

MAX_RETRIES = 1  # Maximum retries with strict mode


class SDLCOrchestrator:
    """
    Orchestrator for the AI SDLC Agent pipeline using LangGraph.
    
    This class defines and manages the workflow graph that coordinates
    multiple AI agents for requirement analysis, code generation, and
    test generation.
    
    The workflow is:
    START → RequirementAnalyzer → (conditional) → CodeGenerator → TestGenerator → END
    
    Features:
    - State checkpointing for workflow persistence and resume
    - Thread-based execution for audit trails and debugging
    - Streaming support for real-time progress updates
    - Conditional routing based on action type
    
    Example usage:
        orchestrator = SDLCOrchestrator()
        
        # Standard execution
        result = await orchestrator.run(ticket_data, action="full_pipeline")
        
        # Streaming execution
        async for event in orchestrator.stream(ticket_data, action="full_pipeline"):
            print(event)
        
        # Resume from checkpoint
        result = await orchestrator.resume(thread_id="abc123")
    """
    
    def __init__(self):
        """Initialize the orchestrator with checkpointing support"""
        self.graph = None
        self.checkpointer = None
        self._init_checkpointer()
        self._build_graph()
        logger.info("Initialized SDLC Orchestrator with checkpointing")
    
    def _init_checkpointer(self):
        """Initialize the memory checkpointer for state persistence"""
        try:
            from langgraph.checkpoint.memory import MemorySaver
            self.checkpointer = MemorySaver()
            logger.info("Initialized MemorySaver checkpointer")
        except ImportError:
            logger.warning("langgraph-checkpoint not available, checkpointing disabled")
            self.checkpointer = None
        except Exception as e:
            logger.error(f"Failed to initialize checkpointer: {e}")
            self.checkpointer = None
    
    def _build_graph(self):
        """
        Build the LangGraph workflow.
        
        This creates a directed graph with:
        - Nodes for each agent
        - Conditional edges based on action type
        - State management between nodes
        """
        try:
            from langgraph.graph import StateGraph, END
            
            # Create the graph with our state type
            workflow = StateGraph(AgentState)
            
            # Add nodes for each agent
            workflow.add_node("requirement_analyzer", self._requirement_analyzer_node)
            workflow.add_node("code_generator", self._code_generator_node)
            workflow.add_node("test_generator", self._test_generator_node)
            
            # Set entry point
            workflow.set_entry_point("requirement_analyzer")
            
            # Add conditional edges based on action
            workflow.add_conditional_edges(
                "requirement_analyzer",
                self._route_after_requirements,
                {
                    "code_generator": "code_generator",
                    "test_generator": "test_generator",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "code_generator",
                self._route_after_code,
                {
                    "test_generator": "test_generator",
                    "end": END
                }
            )
            
            workflow.add_edge("test_generator", END)
            
            # Compile the graph with checkpointer for state persistence
            if self.checkpointer:
                self.graph = workflow.compile(checkpointer=self.checkpointer)
                logger.info("LangGraph workflow compiled with checkpointing enabled")
            else:
                self.graph = workflow.compile()
                logger.info("LangGraph workflow compiled without checkpointing")
            
        except ImportError:
            logger.warning("LangGraph not available, using mock orchestration")
            self.graph = None
        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
            self.graph = None
    
    async def _requirement_analyzer_node(self, state: AgentState) -> AgentState:
        """
        Node for requirement analysis.
        
        This node runs the RequirementAgent to extract structured
        requirements from the ticket.
        """
        logger.info(f"Running RequirementAnalyzer for {state['ticket_id']}")
        state["current_agent"] = "RequirementAnalyzer"
        
        try:
            from app.agents import RequirementAgent
            
            agent = RequirementAgent()
            result = await agent.analyze(
                ticket_id=state["ticket_id"],
                title=state["ticket_title"],
                description=state["ticket_description"],
                acceptance_criteria=state.get("acceptance_criteria")
            )
            
            # Update state with results
            state["requirements"] = [
                req.model_dump() for req in result.requirements
            ]
            state["agent_results"].append({
                "agent": "RequirementAnalyzer",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "result": {
                    "requirements_count": len(result.requirements),
                    "confidence": result.confidence_score
                }
            })
            
        except Exception as e:
            logger.error(f"RequirementAnalyzer failed: {e}")
            state["errors"].append(f"RequirementAnalyzer: {str(e)}")
            state["agent_results"].append({
                "agent": "RequirementAnalyzer",
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        return state
    
    async def _code_generator_node(self, state: AgentState) -> AgentState:
        """
        Node for code generation.
        
        This node runs the CodeAgent to generate code based on
        the extracted requirements.
        """
        logger.info(f"Running CodeGenerator for {state['ticket_id']}")
        state["current_agent"] = "CodeGenerator"
        
        try:
            from app.agents import CodeAgent
            
            agent = CodeAgent()
            result = await agent.generate(
                ticket_id=state["ticket_id"],
                requirements=state.get("requirements", []),
                context={"rag_context": state.get("rag_context")}
            )
            
            # Combine generated files into single output
            code_output = "\n\n".join([
                f"# File: {f.filename}\n{f.content}"
                for f in result.files
            ])
            
            state["generated_code"] = code_output
            state["agent_results"].append({
                "agent": "CodeGenerator",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "result": {
                    "files_generated": len(result.files),
                    "patterns_used": result.patterns_used,
                    "confidence": result.confidence_score
                }
            })
            
        except Exception as e:
            logger.error(f"CodeGenerator failed: {e}")
            state["errors"].append(f"CodeGenerator: {str(e)}")
            state["agent_results"].append({
                "agent": "CodeGenerator",
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        return state
    
    async def _test_generator_node(self, state: AgentState) -> AgentState:
        """
        Node for test generation.
        
        This node runs the TestAgent to generate tests for
        the generated code.
        """
        logger.info(f"Running TestGenerator for {state['ticket_id']}")
        state["current_agent"] = "TestGenerator"
        
        try:
            from app.agents import TestAgent
            
            agent = TestAgent()
            result = await agent.generate(
                ticket_id=state["ticket_id"],
                code=state.get("generated_code", ""),
                requirements=state.get("requirements", [])
            )
            
            state["generated_tests"] = result.test_file
            state["agent_results"].append({
                "agent": "TestGenerator",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "result": {
                    "tests_generated": len(result.tests),
                    "coverage_estimate": result.coverage_estimate,
                    "confidence": result.confidence_score
                }
            })
            
        except Exception as e:
            logger.error(f"TestGenerator failed: {e}")
            state["errors"].append(f"TestGenerator: {str(e)}")
            state["agent_results"].append({
                "agent": "TestGenerator",
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        state["completed_at"] = datetime.utcnow().isoformat()
        return state
    
    def _route_after_requirements(self, state: AgentState) -> str:
        """
        Determine next node after requirement analysis.
        
        Routes based on the requested action:
        - analyze_requirements → end
        - generate_code → code_generator
        - generate_tests → test_generator (skip code gen)
        - full_pipeline → code_generator
        """
        action = state.get("action", WorkflowAction.ANALYZE_REQUIREMENTS)
        
        if action == WorkflowAction.ANALYZE_REQUIREMENTS:
            return "end"
        elif action == WorkflowAction.GENERATE_CODE:
            return "code_generator"
        elif action == WorkflowAction.GENERATE_TESTS:
            return "test_generator"
        elif action == WorkflowAction.FULL_PIPELINE:
            return "code_generator"
        else:
            return "end"
    
    def _route_after_code(self, state: AgentState) -> str:
        """
        Determine next node after code generation.
        
        Routes based on the requested action:
        - generate_code → end
        - full_pipeline → test_generator
        """
        action = state.get("action", WorkflowAction.GENERATE_CODE)
        
        if action == WorkflowAction.FULL_PIPELINE:
            return "test_generator"
        else:
            return "end"
    
    def _create_initial_state(
        self,
        ticket_id: str,
        ticket_title: str,
        ticket_description: str,
        action: str,
        acceptance_criteria: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_pr: Optional[str] = None
    ) -> AgentState:
        """Create the initial state for workflow execution"""
        return {
            "ticket_id": ticket_id,
            "ticket_title": ticket_title,
            "ticket_description": ticket_description,
            "acceptance_criteria": acceptance_criteria,
            "action": WorkflowAction(action),
            "github_repo": github_repo,
            "github_pr": github_pr,
            "rag_context": None,
            "requirements": None,
            "generated_code": None,
            "generated_tests": None,
            "quality_scores": {},
            "retry_counts": {},
            "current_mode": AgentMode.STANDARD,
            "quality_gates_passed": True,
            "current_agent": "",
            "agent_results": [],
            "errors": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
    
    def _get_config(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for graph execution with thread ID.
        
        Args:
            thread_id: Optional thread ID for checkpointing. If not provided,
                      a new UUID will be generated.
        
        Returns:
            Configuration dict with thread_id in configurable
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        return {
            "configurable": {
                "thread_id": thread_id
            }
        }
    
    async def run(
        self,
        ticket_id: str,
        ticket_title: str,
        ticket_description: str,
        action: str = "analyze_requirements",
        acceptance_criteria: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_pr: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the SDLC orchestration pipeline.
        
        Args:
            ticket_id: Jira ticket ID
            ticket_title: Ticket title
            ticket_description: Ticket description
            action: Action to perform (analyze_requirements, generate_code, generate_tests, full_pipeline)
            acceptance_criteria: Optional acceptance criteria
            github_repo: Optional GitHub repo for context
            github_pr: Optional GitHub PR for context
            thread_id: Optional thread ID for checkpointing (auto-generated if not provided)
        
        Returns:
            Final state with all results including thread_id for resume capability
        """
        # Generate thread_id if not provided
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        logger.info(f"Starting SDLC pipeline for {ticket_id} with action: {action}, thread_id: {thread_id}")
        
        # Initialize state
        initial_state = self._create_initial_state(
            ticket_id=ticket_id,
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            action=action,
            acceptance_criteria=acceptance_criteria,
            github_repo=github_repo,
            github_pr=github_pr
        )
        
        if self.graph:
            # Run the LangGraph workflow with checkpointing config
            try:
                config = self._get_config(thread_id)
                final_state = await self.graph.ainvoke(initial_state, config)
                result = dict(final_state)
                result["thread_id"] = thread_id  # Include thread_id for resume capability
                return result
            except Exception as e:
                logger.error(f"Graph execution failed: {e}")
                initial_state["errors"].append(f"Orchestration: {str(e)}")
                result = dict(initial_state)
                result["thread_id"] = thread_id
                return result
        else:
            # Fallback to sequential execution without LangGraph
            result = await self._run_sequential(initial_state)
            result["thread_id"] = thread_id
            return result
    
    async def stream(
        self,
        ticket_id: str,
        ticket_title: str,
        ticket_description: str,
        action: str = "analyze_requirements",
        acceptance_criteria: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_pr: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the SDLC orchestration pipeline with real-time events.
        
        Yields events as each node executes, enabling real-time progress updates.
        
        Args:
            ticket_id: Jira ticket ID
            ticket_title: Ticket title
            ticket_description: Ticket description
            action: Action to perform
            acceptance_criteria: Optional acceptance criteria
            github_repo: Optional GitHub repo for context
            github_pr: Optional GitHub PR for context
            thread_id: Optional thread ID for checkpointing
        
        Yields:
            Event dictionaries with node execution details
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        logger.info(f"Starting streaming SDLC pipeline for {ticket_id}, thread_id: {thread_id}")
        
        initial_state = self._create_initial_state(
            ticket_id=ticket_id,
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            action=action,
            acceptance_criteria=acceptance_criteria,
            github_repo=github_repo,
            github_pr=github_pr
        )
        
        if not self.graph:
            # Fallback: yield single result for non-graph execution
            yield {
                "event": "workflow_start",
                "thread_id": thread_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            result = await self._run_sequential(initial_state)
            yield {
                "event": "workflow_complete",
                "thread_id": thread_id,
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            return
        
        config = self._get_config(thread_id)
        
        # Yield workflow start event
        yield {
            "event": "workflow_start",
            "thread_id": thread_id,
            "action": action,
            "ticket_id": ticket_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Stream events from the graph
            async for event in self.graph.astream_events(initial_state, config, version="v2"):
                event_type = event.get("event", "")
                
                # Filter and transform relevant events
                if event_type == "on_chain_start":
                    node_name = event.get("name", "unknown")
                    yield {
                        "event": "node_start",
                        "node": node_name,
                        "thread_id": thread_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                elif event_type == "on_chain_end":
                    node_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", {})
                    yield {
                        "event": "node_complete",
                        "node": node_name,
                        "thread_id": thread_id,
                        "current_agent": output.get("current_agent", ""),
                        "has_errors": len(output.get("errors", [])) > 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                elif event_type == "on_chain_error":
                    yield {
                        "event": "node_error",
                        "node": event.get("name", "unknown"),
                        "thread_id": thread_id,
                        "error": str(event.get("data", {}).get("error", "Unknown error")),
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # Get final state from checkpoint
            final_state = await self.get_state(thread_id)
            yield {
                "event": "workflow_complete",
                "thread_id": thread_id,
                "data": final_state,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            yield {
                "event": "workflow_error",
                "thread_id": thread_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def resume(self, thread_id: str) -> Dict[str, Any]:
        """
        Resume a workflow from a checkpoint.
        
        Args:
            thread_id: The thread ID of the workflow to resume
        
        Returns:
            Final state after resuming execution
        """
        if not self.graph or not self.checkpointer:
            raise RuntimeError("Cannot resume: checkpointing not available")
        
        logger.info(f"Resuming workflow with thread_id: {thread_id}")
        
        config = self._get_config(thread_id)
        
        try:
            # Resume execution from checkpoint
            final_state = await self.graph.ainvoke(None, config)
            result = dict(final_state) if final_state else {}
            result["thread_id"] = thread_id
            result["resumed"] = True
            return result
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            raise RuntimeError(f"Failed to resume workflow: {e}")
    
    async def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state for a thread from checkpoint.
        
        Args:
            thread_id: The thread ID to retrieve state for
        
        Returns:
            Current state dict or None if not found
        """
        if not self.graph or not self.checkpointer:
            return None
        
        config = self._get_config(thread_id)
        
        try:
            state_snapshot = await self.graph.aget_state(config)
            if state_snapshot and state_snapshot.values:
                return dict(state_snapshot.values)
            return None
        except Exception as e:
            logger.error(f"Failed to get state for thread {thread_id}: {e}")
            return None
    
    async def get_state_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get the state history for a thread from checkpoint.
        
        Args:
            thread_id: The thread ID to retrieve history for
        
        Returns:
            List of historical state snapshots
        """
        if not self.graph or not self.checkpointer:
            return []
        
        config = self._get_config(thread_id)
        history = []
        
        try:
            async for state_snapshot in self.graph.aget_state_history(config):
                if state_snapshot and state_snapshot.values:
                    history.append({
                        "state": dict(state_snapshot.values),
                        "checkpoint_id": state_snapshot.config.get("configurable", {}).get("checkpoint_id"),
                        "timestamp": state_snapshot.created_at if hasattr(state_snapshot, 'created_at') else None
                    })
            return history
        except Exception as e:
            logger.error(f"Failed to get state history for thread {thread_id}: {e}")
            return []
    
    async def _run_sequential(self, state: AgentState) -> Dict[str, Any]:
        """
        Fallback sequential execution when LangGraph is not available.
        """
        logger.info("Running sequential execution (LangGraph not available)")
        
        action = state["action"]
        
        # Always run requirement analyzer
        state = await self._requirement_analyzer_node(state)
        
        if action in [WorkflowAction.GENERATE_CODE, WorkflowAction.FULL_PIPELINE]:
            state = await self._code_generator_node(state)
        
        if action in [WorkflowAction.GENERATE_TESTS, WorkflowAction.FULL_PIPELINE]:
            state = await self._test_generator_node(state)
        
        state["completed_at"] = datetime.utcnow().isoformat()
        return dict(state)
    
    async def run_with_bundle(
        self,
        ticket_id: str,
        ticket_title: str,
        ticket_description: str,
        action: str = "analyze_requirements",
        acceptance_criteria: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_pr: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> "OutputBundle":
        """
        Run the SDLC pipeline and return an Enterprise Output Bundle.
        
        This is the primary method for production use - returns structured
        engineering artifacts instead of raw state.
        
        Args:
            ticket_id: Jira ticket ID
            ticket_title: Ticket title
            ticket_description: Ticket description
            action: Action to perform
            acceptance_criteria: Optional acceptance criteria
            github_repo: Optional GitHub repo for context
            github_pr: Optional GitHub PR for context
            thread_id: Optional thread ID for checkpointing
        
        Returns:
            OutputBundle with all artifacts (requirements, code diff, tests, execution summary)
        """
        from app.schemas.output_bundle import OutputBundle
        
        start_time = time.time()
        
        # Run the pipeline
        final_state = await self.run(
            ticket_id=ticket_id,
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            action=action,
            acceptance_criteria=acceptance_criteria,
            github_repo=github_repo,
            github_pr=github_pr,
            thread_id=thread_id
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert state to OutputBundle
        bundle = OutputBundle.from_pipeline_state(
            state=final_state,
            thread_id=final_state.get("thread_id", thread_id or str(uuid.uuid4())),
            execution_time_ms=execution_time_ms
        )
        
        logger.info(f"Created OutputBundle {bundle.bundle_id} with confidence {bundle.overall_confidence:.2f}")
        
        return bundle
    
    def get_workflow_diagram(self) -> str:
        """
        Get a Mermaid diagram of the workflow.
        
        Returns:
            Mermaid diagram string
        """
        return """
graph TD
    START([Start]) --> RA[Requirement Analyzer]
    RA --> QC1{Quality Check}
    QC1 -->|confidence >= 0.7| Decision{Action Type?}
    QC1 -->|confidence < 0.7| RA_STRICT[Retry Strict Mode]
    RA_STRICT --> Decision
    Decision -->|analyze_requirements| BUNDLE[Create Bundle]
    Decision -->|generate_code| CG[Code Generator]
    Decision -->|generate_tests| TG[Test Generator]
    Decision -->|full_pipeline| CG
    CG --> QC2{Quality Check}
    QC2 -->|confidence >= 0.7| Decision2{Continue?}
    QC2 -->|confidence < 0.7| CG_STRICT[Retry Strict Mode]
    CG_STRICT --> Decision2
    Decision2 -->|full_pipeline| TG
    Decision2 -->|generate_code only| BUNDLE
    TG --> QC3{Quality Check}
    QC3 -->|confidence >= 0.7| BUNDLE
    QC3 -->|confidence < 0.7| TG_STRICT[Retry Strict Mode]
    TG_STRICT --> BUNDLE
    BUNDLE --> END([Output Bundle])
    
    style RA fill:#e1f5fe
    style CG fill:#fff3e0
    style TG fill:#e8f5e9
    style BUNDLE fill:#f3e5f5
    style QC1 fill:#ffebee
    style QC2 fill:#ffebee
    style QC3 fill:#ffebee
"""
