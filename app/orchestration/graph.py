"""
LangGraph Orchestration Module

This module defines the multi-agent workflow using LangGraph.
It coordinates the RequirementAgent, CodeAgent, and TestAgent
in a stateful, inspectable pipeline.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from enum import Enum
from datetime import datetime
from app.utils.logger import logger


class WorkflowAction(str, Enum):
    """Available workflow actions"""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_CODE = "generate_code"
    GENERATE_TESTS = "generate_tests"
    FULL_PIPELINE = "full_pipeline"


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
    
    # Metadata
    current_agent: str
    agent_results: List[Dict[str, Any]]
    errors: List[str]
    started_at: str
    completed_at: Optional[str]


class SDLCOrchestrator:
    """
    Orchestrator for the AI SDLC Agent pipeline using LangGraph.
    
    This class defines and manages the workflow graph that coordinates
    multiple AI agents for requirement analysis, code generation, and
    test generation.
    
    The workflow is:
    START → RequirementAnalyzer → (conditional) → CodeGenerator → TestGenerator → END
    
    Example usage:
        orchestrator = SDLCOrchestrator()
        result = await orchestrator.run(ticket_data, action="full_pipeline")
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.graph = None
        self._build_graph()
        logger.info("Initialized SDLC Orchestrator")
    
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
            
            # Compile the graph
            self.graph = workflow.compile()
            logger.info("LangGraph workflow compiled successfully")
            
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
    
    async def run(
        self,
        ticket_id: str,
        ticket_title: str,
        ticket_description: str,
        action: str = "analyze_requirements",
        acceptance_criteria: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_pr: Optional[str] = None
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
        
        Returns:
            Final state with all results
        """
        logger.info(f"Starting SDLC pipeline for {ticket_id} with action: {action}")
        
        # Initialize state
        initial_state: AgentState = {
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
            "current_agent": "",
            "agent_results": [],
            "errors": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
        
        if self.graph:
            # Run the LangGraph workflow
            try:
                final_state = await self.graph.ainvoke(initial_state)
                return dict(final_state)
            except Exception as e:
                logger.error(f"Graph execution failed: {e}")
                initial_state["errors"].append(f"Orchestration: {str(e)}")
                return dict(initial_state)
        else:
            # Fallback to sequential execution without LangGraph
            return await self._run_sequential(initial_state)
    
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
    
    def get_workflow_diagram(self) -> str:
        """
        Get a Mermaid diagram of the workflow.
        
        Returns:
            Mermaid diagram string
        """
        return """
graph TD
    START([Start]) --> RA[Requirement Analyzer]
    RA --> Decision{Action Type?}
    Decision -->|analyze_requirements| END1([End])
    Decision -->|generate_code| CG[Code Generator]
    Decision -->|generate_tests| TG[Test Generator]
    Decision -->|full_pipeline| CG
    CG --> Decision2{Continue?}
    Decision2 -->|full_pipeline| TG
    Decision2 -->|generate_code only| END2([End])
    TG --> END3([End])
    
    style RA fill:#e1f5fe
    style CG fill:#fff3e0
    style TG fill:#e8f5e9
"""
