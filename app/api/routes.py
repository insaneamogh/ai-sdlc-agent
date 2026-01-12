"""
API Routes Module

This module defines all API endpoints for the AI SDLC Agent.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from app.services.github_service import GitHubService

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
    # Top-level GitHub context to include in response
    github_pr = None
    github_diff = None
    github_files: List[Dict[str, Any]] = []
    generated_code = None
    
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
    # If GitHub context was provided, fetch PR/diff/files and include in agent results
    if request.github_pr or request.github_repo:
        gh_service = GitHubService()
        try:
            if request.github_pr:
                # Support formats: full URL, or owner/repo#number
                pr_number = None
                repo_ref = None

                # owner/repo#number
                if "#" in request.github_pr and "/" in request.github_pr.split("#")[0]:
                    try:
                        parts = request.github_pr.split("#")
                        repo_ref = parts[0]
                        pr_number = int(parts[1])
                    except Exception:
                        pr_number = None

                # URL form
                if pr_number is None:
                    try:
                        segs = request.github_pr.rstrip("/").split("/")
                        pr_number = int(segs[-1])
                        repo_url = "/".join(segs[:-2])
                        owner, repo_name = gh_service._parse_repo_url(repo_url)
                        repo_ref = f"{owner}/{repo_name}" if owner and repo_name else repo_url
                    except Exception:
                        pr_number = None

                pr_info = None
                pr_diff = None
                files = []
                if pr_number and repo_ref:
                    pr_info = await gh_service.get_pr(repo_ref, pr_number)
                    pr_diff = await gh_service.get_pr_diff(repo_ref, pr_number)
                    files = await gh_service.list_files(repo_ref)

                    # parse added hunks from diff into generated_code
                    generated_from_diff = []
                    if pr_diff:
                        current_file = None
                        hunk_lines = []
                        for line in pr_diff.splitlines():
                            if line.startswith('diff --git'):
                                # flush previous
                                if current_file and hunk_lines:
                                    generated_from_diff.append(f"# {current_file}\n" + "\n".join(hunk_lines))
                                current_file = None
                                hunk_lines = []
                            elif line.startswith('+++ b/') or line.startswith('+++ '):
                                current_file = line.split('+++ b/')[-1].strip()
                            elif line.startswith('+') and not line.startswith('+++'):
                                hunk_lines.append(line[1:])
                        if current_file and hunk_lines:
                            generated_from_diff.append(f"# {current_file}\n" + "\n".join(hunk_lines))

                    mock_agents.append(
                        AgentResult(
                            agent_name="GitHubFetcher",
                            status=AgentStatus.COMPLETED,
                            started_at=datetime.utcnow(),
                            completed_at=datetime.utcnow(),
                            result={
                                "pr": pr_info.dict() if pr_info else None,
                                "diff": pr_diff,
                                "files": files
                            }
                        )
                    )
                    github_pr = pr_info.dict() if pr_info else None
                    github_diff = pr_diff
                    github_files = files
                    if pr_diff and generated_from_diff:
                        generated_code = "\n\n---\n\n".join(generated_from_diff)
            else:
                # Only a repo was provided: list files at repo root
                owner, repo_name = gh_service._parse_repo_url(request.github_repo)
                repo_ref = f"{owner}/{repo_name}" if owner and repo_name else request.github_repo
                files = await gh_service.list_files(repo_ref)
                # Attempt to fetch contents of a few useful files to populate generated_code
                fetched_contents = []
                try:
                    # Prefer README.md if present
                    readme_path = None
                    for f in files:
                        if f.get("name", "").lower().startswith("readme"):
                            readme_path = f.get("path")
                            break

                    if readme_path:
                        rf = await gh_service.get_file(repo_ref, readme_path)
                        if rf and rf.content:
                            fetched_contents.append(f"# {readme_path}\n" + rf.content)

                    # Fetch up to 4 top-level code files (.py, .md, .txt, .json)
                    fetched = 0
                    for f in files:
                        if fetched >= 4:
                            break
                        if f.get("type") != "file":
                            continue
                        path = f.get("path")
                        if path and path.lower().endswith(('.py', '.md', '.txt', '.json', '.yaml', '.yml')) and path != readme_path:
                            try:
                                gf = await gh_service.get_file(repo_ref, path)
                                if gf and gf.content:
                                    fetched_contents.append(f"# {path}\n" + gf.content)
                                    fetched += 1
                            except Exception:
                                continue
                except Exception:
                    fetched_contents = []

                mock_agents.append(
                    AgentResult(
                        agent_name="GitHubFetcher",
                        status=AgentStatus.COMPLETED,
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                        result={"files": files}
                    )
                )
                github_pr = None
                github_diff = None
                github_files = files
                # If we fetched any file contents, set generated_code to their concatenation
                if not github_diff and fetched_contents:
                    generated_code = "\n\n---\n\n".join(fetched_contents)
                else:
                    generated_code = None
        except Exception as e:
            mock_agents.append(
                AgentResult(
                    agent_name="GitHubFetcher",
                    status=AgentStatus.FAILED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error=str(e)
                )
            )
        finally:
            try:
                await gh_service.close()
            except Exception:
                pass

    return AnalyzeResponse(
        request_id=request_id,
        ticket_id=request.ticket_id,
        action=request.action,
        status=AgentStatus.COMPLETED,
        agents=mock_agents,
        requirements=mock_requirements,
        generated_code=github_diff or generated_code or "# Generated code will appear here\ndef authenticate_user():\n    pass",
        generated_tests="# Generated tests will appear here\ndef test_authenticate_user():\n    pass",
        github_pr=github_pr,
        github_diff=github_diff,
        github_files=github_files,
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
