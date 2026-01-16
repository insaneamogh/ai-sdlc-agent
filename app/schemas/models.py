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


# ===========================================
# Enhanced Artifact Models
# ===========================================

class DiffType(str, Enum):
    """Types of diff rendering"""
    UNIFIED = "unified"
    SPLIT = "split"
    SEMANTIC = "semantic"


class BreakingChangeRisk(str, Enum):
    """Risk levels for breaking changes"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RAGSource(BaseModel):
    """
    Source document used for RAG-based generation.
    
    Tracks which existing code patterns or documentation
    informed the AI's generation decisions.
    """
    file_path: str = Field(description="Path to the source file")
    similarity_score: float = Field(
        description="Similarity score (0-1) indicating relevance",
        ge=0.0,
        le=1.0
    )
    snippet: Optional[str] = Field(
        default=None,
        description="Relevant code snippet from the source"
    )
    line_range: Optional[tuple] = Field(
        default=None,
        description="Line range (start, end) of the relevant section"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/handlers/AccountHandler.cls",
                "similarity_score": 0.87,
                "snippet": "public class AccountHandler { ... }",
                "line_range": [1, 50]
            }
        }


class ImpactAnalysis(BaseModel):
    """
    Analysis of the impact of code changes.
    
    Helps reviewers understand the scope and risk of changes.
    """
    affected_classes: List[str] = Field(
        default=[],
        description="Classes that may be affected by this change"
    )
    affected_tests: List[str] = Field(
        default=[],
        description="Test files that should be run/updated"
    )
    affected_flows: List[str] = Field(
        default=[],
        description="Business flows that may be impacted"
    )
    breaking_change_risk: BreakingChangeRisk = Field(
        default=BreakingChangeRisk.NONE,
        description="Risk level for breaking changes"
    )
    suggested_review_focus: List[str] = Field(
        default=[],
        description="Areas reviewers should focus on"
    )
    deployment_considerations: List[str] = Field(
        default=[],
        description="Things to consider during deployment"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "affected_classes": ["AccountService", "AccountController"],
                "affected_tests": ["AccountServiceTest", "AccountControllerTest"],
                "affected_flows": ["Account Creation", "Account Update"],
                "breaking_change_risk": "low",
                "suggested_review_focus": ["Error handling", "Null checks"],
                "deployment_considerations": ["Run data migration first"]
            }
        }


class DiffLine(BaseModel):
    """A single line in a diff"""
    line_number: Optional[int] = Field(
        default=None,
        description="Line number in the file"
    )
    old_line_number: Optional[int] = Field(
        default=None,
        description="Line number in the old version"
    )
    new_line_number: Optional[int] = Field(
        default=None,
        description="Line number in the new version"
    )
    type: str = Field(
        description="Line type: 'add', 'remove', 'context', 'header'"
    )
    content: str = Field(description="Line content")
    reasoning: Optional[str] = Field(
        default=None,
        description="AI reasoning for this specific change"
    )


class DiffHunk(BaseModel):
    """A hunk (section) of changes in a diff"""
    old_start: int = Field(description="Starting line in old file")
    old_count: int = Field(description="Number of lines in old file")
    new_start: int = Field(description="Starting line in new file")
    new_count: int = Field(description="Number of lines in new file")
    changes: List[DiffLine] = Field(
        default=[],
        description="Lines in this hunk"
    )
    semantic_label: Optional[str] = Field(
        default=None,
        description="Semantic description of change type",
        examples=["method_addition", "import_change", "refactor", "bug_fix"]
    )
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary of what this hunk changes"
    )


class DiffMetadata(BaseModel):
    """
    Metadata enriching a diff with AI-generated context.
    
    Provides transparency into why changes were made and
    what informed the AI's decisions.
    """
    reasoning_trace: List[str] = Field(
        default=[],
        description="Step-by-step reasoning for the changes"
    )
    rag_sources: List[RAGSource] = Field(
        default=[],
        description="Source documents that informed the changes"
    )
    impact_analysis: Optional[ImpactAnalysis] = Field(
        default=None,
        description="Analysis of change impact"
    )
    confidence_score: float = Field(
        default=0.0,
        description="AI confidence in the changes (0-1)",
        ge=0.0,
        le=1.0
    )
    generation_model: Optional[str] = Field(
        default=None,
        description="Model used to generate the changes"
    )
    generation_timestamp: Optional[datetime] = Field(
        default=None,
        description="When the changes were generated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reasoning_trace": [
                    "Analyzed 3 similar patterns from codebase",
                    "Applied trigger handler best practice",
                    "Added null checks based on existing patterns"
                ],
                "rag_sources": [],
                "confidence_score": 0.94,
                "generation_model": "gpt-4",
                "generation_timestamp": "2024-01-15T10:30:00Z"
            }
        }


class DiffArtifact(BaseModel):
    """
    Enhanced diff artifact with metadata and reasoning.
    
    Represents code changes with full context about why
    changes were made and their potential impact.
    """
    file_path: str = Field(description="Path to the file being changed")
    diff_type: DiffType = Field(
        default=DiffType.UNIFIED,
        description="Type of diff rendering"
    )
    hunks: List[DiffHunk] = Field(
        default=[],
        description="Diff hunks (sections of changes)"
    )
    metadata: DiffMetadata = Field(
        default_factory=DiffMetadata,
        description="Metadata about the changes"
    )
    raw_diff: Optional[str] = Field(
        default=None,
        description="Raw unified diff string"
    )
    old_content: Optional[str] = Field(
        default=None,
        description="Original file content"
    )
    new_content: Optional[str] = Field(
        default=None,
        description="New file content after changes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "force-app/main/default/classes/AccountHandler.cls",
                "diff_type": "unified",
                "hunks": [],
                "metadata": {},
                "raw_diff": "--- a/AccountHandler.cls\n+++ b/AccountHandler.cls\n..."
            }
        }


class StateDiagramFormat(str, Enum):
    """Output formats for state diagrams"""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    DOT = "dot"
    JSON = "json"


class StateNode(BaseModel):
    """A node (state) in a state machine diagram"""
    id: str = Field(description="Unique identifier for the state")
    name: str = Field(description="Display name of the state")
    description: Optional[str] = Field(
        default=None,
        description="Description of what this state represents"
    )
    is_initial: bool = Field(
        default=False,
        description="Whether this is the initial state"
    )
    is_final: bool = Field(
        default=False,
        description="Whether this is a final state"
    )
    metadata: Dict[str, Any] = Field(
        default={},
        description="Additional metadata about the state"
    )


class StateTransition(BaseModel):
    """A transition between states in a state machine"""
    id: str = Field(description="Unique identifier for the transition")
    from_state: str = Field(description="Source state ID")
    to_state: str = Field(description="Target state ID")
    trigger: Optional[str] = Field(
        default=None,
        description="Event/action that triggers this transition"
    )
    condition: Optional[str] = Field(
        default=None,
        description="Guard condition for the transition"
    )
    action: Optional[str] = Field(
        default=None,
        description="Action performed during transition"
    )


class StateDiagramArtifact(BaseModel):
    """
    State machine diagram artifact.
    
    Generated from analyzing code patterns like triggers,
    flows, and process builders to visualize state transitions.
    """
    artifact_type: str = Field(
        default="state_diagram",
        description="Type of artifact"
    )
    format: StateDiagramFormat = Field(
        default=StateDiagramFormat.MERMAID,
        description="Output format of the diagram"
    )
    title: str = Field(
        default="State Machine Diagram",
        description="Title of the diagram"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of what this diagram represents"
    )
    states: List[StateNode] = Field(
        default=[],
        description="States in the state machine"
    )
    transitions: List[StateTransition] = Field(
        default=[],
        description="Transitions between states"
    )
    content: str = Field(
        default="",
        description="Rendered diagram content (e.g., Mermaid syntax)"
    )
    source_files: List[str] = Field(
        default=[],
        description="Files that were analyzed to generate this diagram"
    )
    detected_patterns: List[str] = Field(
        default=[],
        description="Patterns detected during analysis"
    )
    metadata: Dict[str, Any] = Field(
        default={},
        description="Additional metadata"
    )
    interactive_url: Optional[str] = Field(
        default=None,
        description="URL to interactive visualization"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "state_diagram",
                "format": "mermaid",
                "title": "Account Status Flow",
                "states": [
                    {"id": "draft", "name": "Draft", "is_initial": True},
                    {"id": "active", "name": "Active"},
                    {"id": "closed", "name": "Closed", "is_final": True}
                ],
                "transitions": [
                    {"id": "t1", "from_state": "draft", "to_state": "active", "trigger": "activate()"}
                ],
                "content": "stateDiagram-v2\n  [*] --> Draft\n  Draft --> Active: activate()\n  Active --> Closed: close()\n  Closed --> [*]",
                "source_files": ["AccountTrigger.trigger", "AccountHandler.cls"]
            }
        }


class CodeArtifact(BaseModel):
    """
    Enhanced code artifact with confidence and metadata.
    
    Extends basic code output with AI confidence scores,
    reasoning traces, and RAG source attribution.
    """
    artifact_type: str = Field(
        default="code",
        description="Type of artifact"
    )
    filename: str = Field(description="Name of the generated file")
    file_path: Optional[str] = Field(
        default=None,
        description="Full path where file should be placed"
    )
    language: str = Field(description="Programming language")
    content: str = Field(description="Generated code content")
    description: str = Field(description="Description of what the code does")
    line_count: int = Field(default=0)
    
    # Enhanced metadata
    confidence_score: float = Field(
        default=0.0,
        description="AI confidence in the generated code (0-1)",
        ge=0.0,
        le=1.0
    )
    patterns_used: List[str] = Field(
        default=[],
        description="Design patterns used in the code"
    )
    reasoning_trace: List[str] = Field(
        default=[],
        description="Step-by-step reasoning for code decisions"
    )
    rag_sources: List[RAGSource] = Field(
        default=[],
        description="Source documents that informed the code"
    )
    
    # Quality indicators
    has_tests: bool = Field(
        default=False,
        description="Whether tests were generated for this code"
    )
    test_coverage_estimate: Optional[float] = Field(
        default=None,
        description="Estimated test coverage percentage"
    )
    complexity_score: Optional[str] = Field(
        default=None,
        description="Code complexity indicator (low/medium/high)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "code",
                "filename": "AccountTriggerHandler.cls",
                "file_path": "force-app/main/default/classes/AccountTriggerHandler.cls",
                "language": "apex",
                "content": "public class AccountTriggerHandler { ... }",
                "description": "Trigger handler for Account object",
                "line_count": 150,
                "confidence_score": 0.94,
                "patterns_used": ["trigger_handler", "service_layer"],
                "reasoning_trace": [
                    "Analyzed existing trigger patterns",
                    "Applied bulkification best practices"
                ],
                "has_tests": True,
                "test_coverage_estimate": 85.0,
                "complexity_score": "medium"
            }
        }


class TestArtifact(BaseModel):
    """
    Enhanced test artifact with coverage mapping.
    
    Extends basic test output with coverage information
    and requirement traceability.
    """
    artifact_type: str = Field(
        default="test",
        description="Type of artifact"
    )
    filename: str = Field(description="Name of the test file")
    file_path: Optional[str] = Field(
        default=None,
        description="Full path where test file should be placed"
    )
    language: str = Field(description="Programming language")
    content: str = Field(description="Test file content")
    
    # Test details
    test_count: int = Field(
        default=0,
        description="Number of test methods"
    )
    test_methods: List[TestOutput] = Field(
        default=[],
        description="Individual test method details"
    )
    
    # Coverage information
    target_files: List[str] = Field(
        default=[],
        description="Files these tests are designed to cover"
    )
    coverage_estimate: float = Field(
        default=0.0,
        description="Estimated coverage percentage",
        ge=0.0,
        le=100.0
    )
    covered_requirements: List[str] = Field(
        default=[],
        description="Requirement IDs covered by these tests"
    )
    
    # Quality indicators
    confidence_score: float = Field(
        default=0.0,
        description="AI confidence in test quality (0-1)",
        ge=0.0,
        le=1.0
    )
    assertion_count: int = Field(
        default=0,
        description="Total number of assertions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "test",
                "filename": "AccountTriggerHandlerTest.cls",
                "language": "apex",
                "content": "@isTest public class AccountTriggerHandlerTest { ... }",
                "test_count": 5,
                "target_files": ["AccountTriggerHandler.cls"],
                "coverage_estimate": 85.0,
                "covered_requirements": ["REQ-001", "REQ-002"],
                "confidence_score": 0.91,
                "assertion_count": 15
            }
        }


class RequirementArtifact(BaseModel):
    """
    Enhanced requirement artifact with traceability.
    
    Wraps extracted requirements with metadata about
    extraction confidence and source attribution.
    """
    artifact_type: str = Field(
        default="requirements",
        description="Type of artifact"
    )
    ticket_id: str = Field(description="Source ticket ID")
    requirements: List[RequirementOutput] = Field(
        default=[],
        description="Extracted requirements"
    )
    
    # Extraction metadata
    confidence_score: float = Field(
        default=0.0,
        description="Overall confidence in extraction (0-1)",
        ge=0.0,
        le=1.0
    )
    extraction_notes: List[str] = Field(
        default=[],
        description="Notes about the extraction process"
    )
    ambiguities: List[str] = Field(
        default=[],
        description="Identified ambiguities in requirements"
    )
    assumptions: List[str] = Field(
        default=[],
        description="Assumptions made during extraction"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "requirements",
                "ticket_id": "PROJ-123",
                "requirements": [],
                "confidence_score": 0.88,
                "extraction_notes": ["Clear acceptance criteria provided"],
                "ambiguities": ["Unclear error handling requirements"],
                "assumptions": ["Standard authentication flow assumed"]
            }
        }


class ArtifactBundle(BaseModel):
    """
    Complete bundle of all artifacts from a pipeline run.
    
    Aggregates all generated artifacts with their metadata
    for comprehensive output and review.
    """
    bundle_id: str = Field(description="Unique bundle identifier")
    thread_id: Optional[str] = Field(
        default=None,
        description="Workflow thread ID for checkpointing"
    )
    ticket_id: str = Field(description="Source ticket ID")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the bundle was created"
    )
    
    # Artifacts
    requirements: Optional[RequirementArtifact] = Field(
        default=None,
        description="Extracted requirements"
    )
    code_artifacts: List[CodeArtifact] = Field(
        default=[],
        description="Generated code files"
    )
    test_artifacts: List[TestArtifact] = Field(
        default=[],
        description="Generated test files"
    )
    diff_artifacts: List[DiffArtifact] = Field(
        default=[],
        description="Code diffs with metadata"
    )
    state_diagrams: List[StateDiagramArtifact] = Field(
        default=[],
        description="Generated state machine diagrams"
    )
    
    # Summary metrics
    total_files_generated: int = Field(
        default=0,
        description="Total number of files generated"
    )
    total_lines_of_code: int = Field(
        default=0,
        description="Total lines of code generated"
    )
    average_confidence: float = Field(
        default=0.0,
        description="Average confidence across all artifacts"
    )
    
    # Execution metadata
    pipeline_duration_seconds: Optional[float] = Field(
        default=None,
        description="Total pipeline execution time"
    )
    agents_executed: List[str] = Field(
        default=[],
        description="List of agents that executed"
    )
    errors: List[str] = Field(
        default=[],
        description="Any errors encountered"
    )
    warnings: List[str] = Field(
        default=[],
        description="Any warnings generated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "bundle_id": "bundle-abc123",
                "thread_id": "thread-xyz789",
                "ticket_id": "PROJ-123",
                "created_at": "2024-01-15T10:30:00Z",
                "requirements": None,
                "code_artifacts": [],
                "test_artifacts": [],
                "diff_artifacts": [],
                "state_diagrams": [],
                "total_files_generated": 3,
                "total_lines_of_code": 450,
                "average_confidence": 0.91,
                "pipeline_duration_seconds": 45.2,
                "agents_executed": ["RequirementAnalyzer", "CodeGenerator", "TestGenerator"],
                "errors": [],
                "warnings": []
            }
        }
