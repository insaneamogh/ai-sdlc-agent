#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
Pydantic Models Module

This module contains all the Pydantic models used for data validation
and serialization throughout the AI SDLC Agent application.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ===========================================
# Enums
# ===========================================

class ActionType(str, Enum):
    """Available actions for the SDLC pipeline"""
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    GENERATE_CODE = "generate_code"
    GENERATE_TESTS = "generate_tests"
    FULL_PIPELINE = "full_pipeline"


class RequirementType(str, Enum):
    """Types of requirements"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non-functional"
    CONSTRAINT = "constraint"


class Priority(str, Enum):
    """Priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentStatus(str, Enum):
    """Status of agent execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ===========================================
# Input Models
# ===========================================

class TicketInput(BaseModel):
    """
    Input model for a ticket to be analyzed.
    
    This can be from Jira or manually provided.
    """
    ticket_id: str = Field(
        ...,
        description="Unique identifier for the ticket",
        example="PROJ-123"
    )
    title: str = Field(
        ...,
        description="Title of the ticket",
        example="Implement user authentication"
    )
    description: str = Field(
        ...,
        description="Detailed description of the ticket"
    )
    acceptance_criteria: Optional[str] = Field(
        default=None,
        description="Acceptance criteria for the ticket"
    )
    labels: List[str] = Field(
        default=[],
        description="Labels/tags associated with the ticket"
    )
    priority: Optional[Priority] = Field(
        default=None,
        description="Priority of the ticket"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "PROJ-123",
                "title": "Implement user authentication",
                "description": "As a user, I want to log in securely...",
                "acceptance_criteria": "Given valid credentials...",
                "labels": ["authentication", "security"],
                "priority": "high"
            }
        }


class GitHubContext(BaseModel):
    """Context from GitHub for code generation"""
    repo_url: Optional[str] = Field(
        default=None,
        description="GitHub repository URL"
    )
    pr_url: Optional[str] = Field(
        default=None,
        description="GitHub PR URL for additional context"
    )
    branch: str = Field(
        default="main",
        description="Branch to use for context"
    )


class PipelineInput(BaseModel):
    """Input for running the SDLC pipeline"""
    ticket: TicketInput
    action: ActionType = Field(
        default=ActionType.ANALYZE_REQUIREMENTS,
        description="Action to perform"
    )
    github_context: Optional[GitHubContext] = Field(
        default=None,
        description="Optional GitHub context"
    )
    options: Dict[str, Any] = Field(
        default={},
        description="Additional options for the pipeline"
    )


# ===========================================
# Output Models
# ===========================================

class RequirementOutput(BaseModel):
    """Output model for an extracted requirement"""
    id: str = Field(description="Unique requirement ID")
    type: RequirementType = Field(description="Type of requirement")
    description: str = Field(description="Requirement description")
    priority: Priority = Field(default=Priority.MEDIUM)
    acceptance_criteria: List[str] = Field(default=[])
    edge_cases: List[str] = Field(default=[])
    source: str = Field(
        default="extracted",
        description="Source of the requirement"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "REQ-001",
                "type": "functional",
                "description": "User must be able to authenticate using OAuth 2.0",
                "priority": "high",
                "acceptance_criteria": ["User can login", "Session is created"],
                "edge_cases": ["Invalid credentials", "Expired token"],
                "source": "extracted"
            }
        }


class CodeOutput(BaseModel):
    """Output model for generated code"""
    filename: str = Field(description="Name of the generated file")
    language: str = Field(description="Programming language")
    content: str = Field(description="Generated code content")
    description: str = Field(description="Description of what the code does")
    line_count: int = Field(default=0)
    patterns_used: List[str] = Field(
        default=[],
        description="Design patterns used in the code"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "authentication.py",
                "language": "python",
                "content": "class AuthService:\n    ...",
                "description": "Authentication service implementation",
                "line_count": 50,
                "patterns_used": ["singleton", "factory"]
            }
        }


class TestOutput(BaseModel):
    """Output model for a generated test"""
    name: str = Field(description="Test function name")
    description: str = Field(description="What the test verifies")
    test_type: str = Field(
        default="unit",
        description="Type of test (unit, integration, e2e)"
    )
    code: str = Field(description="Test code")
    covers_requirement: Optional[str] = Field(
        default=None,
        description="Requirement ID this test covers"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "test_authenticate_valid_credentials",
                "description": "Test authentication with valid credentials",
                "test_type": "unit",
                "code": "def test_authenticate_valid_credentials():\n    ...",
                "covers_requirement": "REQ-001"
            }
        }


class AgentResult(BaseModel):
    """Result from a single agent execution"""
    agent_name: str = Field(description="Name of the agent")
    status: AgentStatus = Field(description="Execution status")
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Agent-specific results"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="LLM tokens consumed"
    )


class PipelineResult(BaseModel):
    """
    Complete result from the SDLC pipeline.
    
    This is the main output model that contains all results
    from the multi-agent pipeline execution.
    """
    request_id: str = Field(description="Unique request identifier")
    ticket_id: str = Field(description="Input ticket ID")
    action: ActionType = Field(description="Action that was performed")
    status: AgentStatus = Field(description="Overall pipeline status")
    
    # Agent execution details
    agents: List[AgentResult] = Field(
        default=[],
        description="Results from each agent"
    )
    
    # Extracted requirements
    requirements: List[RequirementOutput] = Field(
        default=[],
        description="Extracted requirements"
    )
    
    # Generated code
    generated_files: List[CodeOutput] = Field(
        default=[],
        description="Generated code files"
    )
    
    # Generated tests
    generated_tests: List[TestOutput] = Field(
        default=[],
        description="Generated test cases"
    )
    
    # Metadata
    started_at: datetime = Field(description="Pipeline start time")
    completed_at: Optional[datetime] = Field(default=None)
    total_duration_seconds: Optional[float] = Field(default=None)
    total_tokens_used: Optional[int] = Field(default=None)
    errors: List[str] = Field(default=[])
    warnings: List[str] = Field(default=[])
    
    # Summary
    summary: str = Field(
        default="",
        description="Human-readable summary of results"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "abc123",
                "ticket_id": "PROJ-123",
                "action": "full_pipeline",
                "status": "completed",
                "agents": [],
                "requirements": [],
                "generated_files": [],
                "generated_tests": [],
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:31:00Z",
                "total_duration_seconds": 60.0,
                "total_tokens_used": 5000,
                "errors": [],
                "warnings": [],
                "summary": "Successfully processed ticket PROJ-123"
            }
        }


# ===========================================
# Utility Models
# ===========================================

class HealthCheck(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "AI SDLC Agent"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None)
    request_id: Optional[str] = Field(default=None)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(default=1)
    page_size: int = Field(default=20)
    has_more: bool = Field(default=False)

#__________________________GenAI: Generated code ends here______________________________#
