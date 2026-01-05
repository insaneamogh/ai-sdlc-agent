#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
API Routes Module

This module defines all API endpoints for the AI SDLC Agent.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

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
    request_id = str(uuid.uuid4())[:8]
    
    # For now, return mock data
    # This will be replaced with actual agent orchestration
    
    mock_requirements = [
        Requirement(
            id="REQ-001",
            type="functional",
            description="User must be able to authenticate using OAuth 2.0",
            priority="high"
        ),
        Requirement(
            id="REQ-002",
            type="functional",
            description="System must validate user credentials against the identity provider",
            priority="high"
        ),
        Requirement(
            id="REQ-003",
            type="non-functional",
            description="Authentication must complete within 3 seconds",
            priority="medium"
        ),
        Requirement(
            id="REQ-004",
            type="constraint",
            description="Must support multi-factor authentication",
            priority="high"
        )
    ]
    
    mock_agents = [
        AgentResult(
            agent_name="RequirementAnalyzer",
            status=AgentStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            result={"requirements_count": len(mock_requirements)}
        )
    ]
    
    if request.action in [ActionType.GENERATE_CODE, ActionType.FULL_PIPELINE]:
        mock_agents.append(
            AgentResult(
                agent_name="CodeGenerator",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                result={"files_generated": 2}
            )
        )
    
    if request.action in [ActionType.GENERATE_TESTS, ActionType.FULL_PIPELINE]:
        mock_agents.append(
            AgentResult(
                agent_name="TestGenerator",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                result={"tests_generated": 5}
            )
        )
    
    return AnalyzeResponse(
        request_id=request_id,
        ticket_id=request.ticket_id,
        action=request.action,
        status=AgentStatus.COMPLETED,
        agents=mock_agents,
        requirements=mock_requirements,
        generated_code="# Generated code will appear here\ndef authenticate_user():\n    pass",
        generated_tests="# Generated tests will appear here\ndef test_authenticate_user():\n    pass",
        message=f"Successfully analyzed ticket {request.ticket_id}"
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


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """
    Get details of a Jira ticket.
    
    This endpoint fetches ticket information from Jira.
    Currently returns mock data.
    """
    # Mock data - will be replaced with actual Jira integration
    return TicketResponse(
        ticket_id=ticket_id,
        title=f"Sample Ticket: {ticket_id}",
        description="This is a sample ticket description. In production, this will be fetched from Jira.",
        status="Open",
        acceptance_criteria="- User can login\n- User can logout\n- Session is maintained",
        linked_prs=["https://github.com/org/repo/pull/42"]
    )


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

#__________________________GenAI: Generated code ends here______________________________#
