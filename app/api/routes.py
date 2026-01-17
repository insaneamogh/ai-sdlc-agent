"""
API Routes Module

This module defines all API endpoints for the AI SDLC Agent.

Enhanced with:
- Server-Sent Events (SSE) streaming for real-time progress
- Workflow state retrieval and resume endpoints
- Thread-based execution tracking
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import json
import asyncio
from app.services.github_service import GitHubService
from app.utils.logger import logger

router = APIRouter()


# ===========================================
# Enums
# ===========================================

class ActionType(str, Enum):
    """Available actions for ticket analysis"""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_CODE = "generate_code"
    GENERATE_TESTS = "generate_tests"
    FULL_PIPELINE = "full_pipeline"


class AgentStatus(str, Enum):
    """Status of agent execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ===========================================
# Request Models
# ===========================================

class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint"""
    ticket_id: str = Field(
        ...,
        description="Jira ticket ID (e.g., PROJ-123)",
        example="PROJ-123"
    )
    action: ActionType = Field(
        default=ActionType.ANALYZE_REQUIREMENTS,
        description="Action to perform on the ticket"
    )
    github_repo: Optional[str] = Field(
        default=None,
        description="GitHub repository URL for code context",
        example="https://github.com/org/repo"
    )
    github_pr: Optional[str] = Field(
        default=None,
        description="GitHub PR URL for additional context",
        example="https://github.com/org/repo/pull/42"
    )
    model: Optional[str] = Field(
        default=None,
        description="OpenAI model to use (e.g., gpt-4o, gpt-5, o1)",
        example="gpt-4o"
    )


class GitHubFileRequest(BaseModel):
    """Request to fetch a single file from a repository"""
    repo: str
    path: str


class TicketInput(BaseModel):
    """Manual ticket input when Jira is not connected"""
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    acceptance_criteria: Optional[str] = Field(
        default=None,
        description="Acceptance criteria"
    )


class ManualAnalyzeRequest(BaseModel):
    """Request model for manual analysis without Jira"""
    ticket: TicketInput
    action: ActionType = Field(default=ActionType.ANALYZE_REQUIREMENTS)


# ===========================================
# Response Models
# ===========================================

class Requirement(BaseModel):
    """Extracted requirement"""
    id: str
    type: str  # functional, non-functional, constraint
    description: str
    priority: Optional[str] = None


class AgentResult(BaseModel):
    """Result from a single agent"""
    agent_name: str
    status: AgentStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint"""
    request_id: str
    ticket_id: str
    action: ActionType
    status: AgentStatus
    agents: List[AgentResult] = []
    requirements: Optional[List[Requirement]] = None
    generated_code: Optional[str] = None
    generated_tests: Optional[str] = None
    github_pr: Optional[Dict[str, Any]] = None
    github_diff: Optional[str] = None
    github_files: Optional[List[Dict[str, Any]]] = None
    message: str


class TicketResponse(BaseModel):
    """Response model for ticket details"""
    ticket_id: str
    title: str
    description: str
    status: str
    acceptance_criteria: Optional[str] = None
    linked_prs: List[str] = []


# ===========================================
# API Endpoints
# ===========================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the API.
    """
    return {
        "status": "healthy",
        "service": "AI SDLC Agent",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_ticket(request: AnalyzeRequest):
    """
    Analyze a Jira ticket and perform the requested action.
    
    This endpoint triggers the AI agent pipeline to:
    - Analyze requirements from the ticket
    - Generate code based on requirements
    - Generate tests for the code
    
    The action parameter determines which agents are executed.
    """
    import uuid
    # Use STRICT orchestrator that ACTUALLY fetches GitHub content
    from app.orchestration import SDLCOrchestrator
    
    request_id = str(uuid.uuid4())[:8]
    
    # Top-level GitHub context to include in response
    github_pr_info = None
    github_diff = None
    github_files: List[Dict[str, Any]] = []
    
    # Fetch GitHub context if provided
    ticket_title = f"Ticket {request.ticket_id}"
    ticket_description = f"Analysis request for ticket {request.ticket_id}"
    
    if request.github_repo:
        gh_service = GitHubService()
        try:
            owner, repo_name = gh_service._parse_repo_url(request.github_repo)
            repo_ref = f"{owner}/{repo_name}" if owner and repo_name else request.github_repo
            github_files = await gh_service.list_files(repo_ref)
            
            # Try to get README for context
            readme_content = ""
            for f in github_files:
                if f.get("name", "").lower().startswith("readme"):
                    try:
                        rf = await gh_service.get_file(repo_ref, f.get("path"))
                        if rf and rf.content:
                            readme_content = rf.content
                            break
                    except Exception:
                        pass
            
            ticket_title = f"Analysis of {repo_ref}"
            ticket_description = f"Repository: {repo_ref}\n\nFiles: {len(github_files)} files found.\n\n{readme_content[:2000] if readme_content else 'No README found.'}"
            
        except Exception as e:
            logger.error(f"Failed to fetch GitHub context: {e}")
        finally:
            try:
                await gh_service.close()
            except Exception:
                pass
    
    # Run the actual orchestrator with model override if provided
    orchestrator = SDLCOrchestrator(model=request.model)
    result = await orchestrator.run(
        ticket_id=request.ticket_id,
        ticket_title=ticket_title,
        ticket_description=ticket_description,
        action=request.action.value,
        github_repo=request.github_repo,
        github_pr=request.github_pr
    )
    
    # Convert orchestrator result to response format
    requirements = []
    if result.get("requirements"):
        for i, req in enumerate(result["requirements"]):
            requirements.append(Requirement(
                id=req.get("id", f"REQ-{i+1:03d}"),
                type=req.get("type", "functional"),
                description=req.get("description", ""),
                priority=req.get("priority", "medium")
            ))
    
    agents = []
    for agent_result in result.get("agent_results", []):
        # Handle both old and new orchestrator keys
        agent_name = agent_result.get("agent_name") or agent_result.get("agent", "Unknown")
        agents.append(AgentResult(
            agent_name=agent_name,
            status=AgentStatus.COMPLETED if agent_result.get("status") == "completed" else AgentStatus.FAILED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            result=agent_result.get("result"),
            error=agent_result.get("error")
        ))
    
    # If no agents ran successfully, add error info
    if not agents:
        agents.append(AgentResult(
            agent_name="Orchestrator",
            status=AgentStatus.FAILED if result.get("errors") else AgentStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error="; ".join(result.get("errors", [])) if result.get("errors") else None
        ))
    
    generated_code = result.get("generated_code") or "# No code generated"
    generated_tests = result.get("generated_tests") or "# No tests generated"

    return AnalyzeResponse(
        request_id=request_id,
        ticket_id=request.ticket_id,
        action=request.action,
        status=AgentStatus.COMPLETED if not result.get("errors") else AgentStatus.FAILED,
        agents=agents,
        requirements=requirements,
        generated_code=generated_code,
        generated_tests=generated_tests,
        github_pr=github_pr_info,
        github_diff=github_diff,
        github_files=github_files,
        message=f"Successfully analyzed ticket {request.ticket_id}" if not result.get("errors") else f"Errors: {'; '.join(result.get('errors', []))}"
    )


@router.post("/analyze/manual", response_model=AnalyzeResponse)
async def analyze_manual(request: ManualAnalyzeRequest):
    """
    Analyze a manually provided ticket (without Jira integration).
    
    Use this endpoint when Jira is not configured or for testing.
    """
    import uuid
    request_id = str(uuid.uuid4())[:8]
    
    # Create a virtual ticket ID
    virtual_ticket_id = f"MANUAL-{request_id}"
    
    mock_requirements = [
        Requirement(
            id="REQ-001",
            type="functional",
            description=f"Extracted from: {request.ticket.title}",
            priority="medium"
        )
    ]
    
    return AnalyzeResponse(
        request_id=request_id,
        ticket_id=virtual_ticket_id,
        action=request.action,
        status=AgentStatus.COMPLETED,
        agents=[
            AgentResult(
                agent_name="RequirementAnalyzer",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                result={"source": "manual_input"}
            )
        ],
        requirements=mock_requirements,
        message=f"Successfully analyzed manual ticket: {request.ticket.title}"
    )


@router.get("/jira/test")
async def test_jira_connection():
    """
    Test the Jira connection and return server info.
    
    Use this endpoint to verify Jira credentials are configured correctly.
    Returns connection status and server information if successful.
    """
    from app.services.jira_service import JiraService
    
    jira = JiraService()
    result = await jira.test_connection()
    await jira.close()
    
    return {
        "service": "Jira",
        "configured": jira.is_configured,
        "is_cloud": jira.is_cloud,
        **result
    }


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """
    Get details of a Jira ticket.
    
    This endpoint fetches ticket information from Jira.
    If Jira is not configured, returns mock data.
    """
    from app.services.jira_service import JiraService
    
    jira = JiraService()
    
    try:
        ticket = await jira.get_ticket(ticket_id)
        
        return TicketResponse(
            ticket_id=ticket.key,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status,
            acceptance_criteria=ticket.acceptance_criteria,
            linked_prs=ticket.linked_prs
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticket: {str(e)}")
    finally:
        await jira.close()


@router.get("/agents")
async def list_agents():
    """
    List all available agents and their capabilities.
    """
    return {
        "agents": [
            {
                "name": "RequirementAnalyzer",
                "description": "Extracts structured requirements from Jira tickets",
                "capabilities": [
                    "Extract functional requirements",
                    "Extract non-functional requirements",
                    "Identify edge cases",
                    "Prioritize requirements"
                ]
            },
            {
                "name": "CodeGenerator",
                "description": "Generates code based on requirements and existing patterns",
                "capabilities": [
                    "Generate code snippets",
                    "Create diff patches",
                    "Follow existing code patterns",
                    "Apply coding standards"
                ]
            },
            {
                "name": "TestGenerator",
                "description": "Creates comprehensive test cases",
                "capabilities": [
                    "Generate unit tests",
                    "Create edge case tests",
                    "Match project test style",
                    "Generate test data"
                ]
            }
        ]
    }


@router.get("/status/{request_id}")
async def get_request_status(request_id: str):
    """
    Get the status of a previous analysis request.
    
    Use this to check on long-running analysis tasks.
    """
    # In production, this would look up the request in a database
    return {
        "request_id": request_id,
        "status": "completed",
        "message": "Request completed successfully"
    }


@router.post("/github/file")
async def fetch_github_file(req: GitHubFileRequest):
    """
    Return file content for a given repo and path.
    
    This endpoint fetches a single file from a GitHub repository.
    """
    gh_service = GitHubService()
    try:
        owner, repo_name = gh_service._parse_repo_url(req.repo)
        repo_ref = f"{owner}/{repo_name}" if owner and repo_name else req.repo
        gf = await gh_service.get_file(repo_ref, req.path)
        if not gf:
            raise HTTPException(status_code=404, detail="File not found")
        return {"path": gf.path, "content": gf.content, "sha": gf.sha, "size": gf.size}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            await gh_service.close()
        except Exception:
            pass


# ===========================================
# Streaming & Workflow Management Endpoints
# ===========================================

class StreamAnalyzeRequest(BaseModel):
    """Request model for streaming analyze endpoint"""
    ticket_id: str = Field(
        ...,
        description="Jira ticket ID (e.g., PROJ-123)",
        example="PROJ-123"
    )
    title: Optional[str] = Field(
        default=None,
        description="Ticket title (optional, will be fetched if not provided)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Ticket description (optional, will be fetched if not provided)"
    )
    action: ActionType = Field(
        default=ActionType.FULL_PIPELINE,
        description="Action to perform on the ticket"
    )
    acceptance_criteria: Optional[str] = Field(
        default=None,
        description="Acceptance criteria for the ticket"
    )
    github_repo: Optional[str] = Field(
        default=None,
        description="GitHub repository URL for code context"
    )
    github_pr: Optional[str] = Field(
        default=None,
        description="GitHub PR URL for additional context"
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID for checkpointing (auto-generated if not provided)"
    )
    model: Optional[str] = Field(
        default=None,
        description="OpenAI model to use (e.g., gpt-4o, gpt-4.1, o1)",
        example="gpt-4o"
    )


class ResumeRequest(BaseModel):
    """Request model for resuming a workflow"""
    thread_id: str = Field(
        ...,
        description="Thread ID of the workflow to resume"
    )


class WorkflowStateResponse(BaseModel):
    """Response model for workflow state"""
    thread_id: str
    ticket_id: Optional[str] = None
    current_agent: Optional[str] = None
    status: str
    requirements: Optional[List[Dict[str, Any]]] = None
    generated_code: Optional[str] = None
    generated_tests: Optional[str] = None
    agent_results: List[Dict[str, Any]] = []
    errors: List[str] = []
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.post("/analyze/stream")
async def analyze_stream(request: StreamAnalyzeRequest):
    """
    Stream the analysis pipeline with real-time Server-Sent Events (SSE).
    
    This endpoint provides real-time progress updates as each agent executes.
    Events are streamed in SSE format for easy consumption by web clients.
    
    Event types:
    - workflow_start: Pipeline has started
    - node_start: An agent node has started execution
    - node_complete: An agent node has completed
    - node_error: An agent node encountered an error
    - workflow_complete: Pipeline has finished with final results
    - workflow_error: Pipeline encountered a fatal error
    
    Example usage with JavaScript:
    ```javascript
    const eventSource = new EventSource('/api/v1/analyze/stream', {
        method: 'POST',
        body: JSON.stringify({ ticket_id: 'PROJ-123', action: 'full_pipeline' })
    });
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.event, data);
    };
    ```
    """
    from app.orchestration import SDLCOrchestrator
    
    # Prepare ticket info
    ticket_title = request.title or f"Ticket {request.ticket_id}"
    ticket_description = request.description or f"Analysis request for ticket {request.ticket_id}"
    
    # Fetch GitHub context if provided
    if request.github_repo and not request.description:
        gh_service = GitHubService()
        try:
            owner, repo_name = gh_service._parse_repo_url(request.github_repo)
            repo_ref = f"{owner}/{repo_name}" if owner and repo_name else request.github_repo
            github_files = await gh_service.list_files(repo_ref)
            
            # Try to get README for context
            readme_content = ""
            for f in github_files:
                if f.get("name", "").lower().startswith("readme"):
                    try:
                        rf = await gh_service.get_file(repo_ref, f.get("path"))
                        if rf and rf.content:
                            readme_content = rf.content
                            break
                    except Exception:
                        pass
            
            ticket_title = f"Analysis of {repo_ref}"
            ticket_description = f"Repository: {repo_ref}\n\nFiles: {len(github_files)} files found.\n\n{readme_content[:2000] if readme_content else 'No README found.'}"
            
        except Exception as e:
            logger.error(f"Failed to fetch GitHub context: {e}")
        finally:
            try:
                await gh_service.close()
            except Exception:
                pass
    
    async def event_generator():
        """Generate SSE events from the orchestrator stream"""
        orchestrator = SDLCOrchestrator(model=request.model)
        
        try:
            async for event in orchestrator.stream(
                ticket_id=request.ticket_id,
                ticket_title=ticket_title,
                ticket_description=ticket_description,
                action=request.action.value,
                acceptance_criteria=request.acceptance_criteria,
                github_repo=request.github_repo,
                github_pr=request.github_pr,
                thread_id=request.thread_id
            ):
                # Format as SSE
                event_data = json.dumps(event, default=str)
                yield f"event: {event.get('event', 'message')}\n"
                yield f"data: {event_data}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_event = {
                "event": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"event: error\n"
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/workflow/{thread_id}/state", response_model=WorkflowStateResponse)
async def get_workflow_state(thread_id: str):
    """
    Get the current state of a workflow by thread ID.
    
    Use this to check the current state of a running or completed workflow.
    The state includes all accumulated results from executed agents.
    """
    from app.orchestration import SDLCOrchestrator
    
    orchestrator = SDLCOrchestrator()
    state = await orchestrator.get_state(thread_id)
    
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"No workflow found with thread_id: {thread_id}"
        )
    
    # Determine status based on state
    status = "unknown"
    if state.get("completed_at"):
        status = "completed" if not state.get("errors") else "failed"
    elif state.get("current_agent"):
        status = "running"
    elif state.get("started_at"):
        status = "started"
    
    return WorkflowStateResponse(
        thread_id=thread_id,
        ticket_id=state.get("ticket_id"),
        current_agent=state.get("current_agent"),
        status=status,
        requirements=state.get("requirements"),
        generated_code=state.get("generated_code"),
        generated_tests=state.get("generated_tests"),
        agent_results=state.get("agent_results", []),
        errors=state.get("errors", []),
        started_at=state.get("started_at"),
        completed_at=state.get("completed_at")
    )


@router.get("/workflow/{thread_id}/history")
async def get_workflow_history(thread_id: str):
    """
    Get the state history of a workflow by thread ID.
    
    Returns a list of all state snapshots captured during workflow execution.
    Useful for debugging and understanding the workflow progression.
    """
    from app.orchestration import SDLCOrchestrator
    
    orchestrator = SDLCOrchestrator()
    history = await orchestrator.get_state_history(thread_id)
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for thread_id: {thread_id}"
        )
    
    return {
        "thread_id": thread_id,
        "history_count": len(history),
        "history": history
    }


@router.post("/workflow/resume")
async def resume_workflow(request: ResumeRequest):
    """
    Resume a paused or interrupted workflow from its last checkpoint.
    
    Use this to continue a workflow that was interrupted or paused.
    The workflow will resume from the last saved state.
    """
    from app.orchestration import SDLCOrchestrator
    
    orchestrator = SDLCOrchestrator()
    
    try:
        result = await orchestrator.resume(request.thread_id)
        
        return {
            "thread_id": request.thread_id,
            "status": "completed" if not result.get("errors") else "failed",
            "resumed": True,
            "result": result
        }
    except RuntimeError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to resume workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume workflow: {str(e)}"
        )


@router.get("/workflow/diagram")
async def get_workflow_diagram():
    """
    Get the Mermaid diagram representation of the workflow.
    
    Returns a Mermaid diagram string that can be rendered to visualize
    the workflow structure and agent relationships.
    """
    from app.orchestration import SDLCOrchestrator
    
    orchestrator = SDLCOrchestrator()
    diagram = orchestrator.get_workflow_diagram()
    
    return {
        "format": "mermaid",
        "diagram": diagram,
        "description": "SDLC Agent Workflow - Shows the flow between RequirementAnalyzer, CodeGenerator, and TestGenerator agents"
    }
