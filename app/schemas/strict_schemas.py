"""
Strict Output Schemas for SDLC Agents - LANGUAGE AGNOSTIC VERSION

These schemas enforce structure WITHOUT language assumptions.
Language, framework, and conventions are INFERRED, not assumed.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ===========================================
# GLOBAL CONSTANTS
# ===========================================

GLOBAL_AGENT_RULES = """
You are an SDLC agent operating on real-world repositories.

Repositories may contain:
- Multiple programming languages
- Multiple frameworks
- Multiple coding styles
- Multiple testing strategies

You MUST:
- Infer language, framework, and conventions from context
- Never assume a default language or framework
- Never hardcode tool choices unless evidence exists
- Explicitly list assumptions when inference is incomplete

You must operate in a language-agnostic manner.
"""


# ===========================================
# REQUIREMENT AGENT SCHEMA (IMPLEMENTATION-NEUTRAL)
# ===========================================

class RequirementPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non-functional"
    CONSTRAINT = "constraint"


class Requirement(BaseModel):
    """
    Single requirement - IMPLEMENTATION NEUTRAL.
    No language, no framework, no technology mentions.
    """
    id: str = Field(..., description="Unique ID like REQ-001, REQ-002")
    type: RequirementType
    description: str = Field(
        ..., 
        min_length=10, 
        description="Clear, actionable requirement - NO implementation details"
    )
    priority: RequirementPriority
    acceptance_criteria: List[str] = Field(
        default_factory=list, 
        description="Testable criteria - behavior, not implementation"
    )
    edge_cases: List[str] = Field(
        default_factory=list,
        description="Edge cases to consider"
    )
    ambiguities: List[str] = Field(
        default_factory=list,
        description="Unclear aspects that need clarification"
    )

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        # Allow REQ-, FUNC-, NFR-, CON- prefixes
        valid_prefixes = ('REQ-', 'FUNC-', 'NFR-', 'CON-')
        if not any(v.startswith(p) for p in valid_prefixes):
            raise ValueError(f'ID must start with one of: {valid_prefixes}')
        return v


class RequirementSpec(BaseModel):
    """
    STRICT output schema for RequirementAgent.
    IMPLEMENTATION NEUTRAL - no language/framework mentions.
    """
    functional_requirements: List[Requirement] = Field(..., min_length=1)
    non_functional_requirements: List[Requirement] = Field(default_factory=list)
    constraints: List[Requirement] = Field(default_factory=list)
    assumptions: List[str] = Field(
        default_factory=list, 
        description="Assumptions made due to incomplete information"
    )
    context_summary: str = Field(
        ..., 
        description="Summary of the problem domain - NO implementation details"
    )
    
    def get_all_requirements(self) -> List[Requirement]:
        """Get all requirements as flat list"""
        return self.functional_requirements + self.non_functional_requirements + self.constraints


# ===========================================
# CODE AGENT SCHEMA (LANGUAGE-AWARE, INFERRED)
# ===========================================

class DiffHunk(BaseModel):
    """
    A single hunk in a unified diff.
    """
    old_start: int = Field(..., description="Starting line in original file")
    old_count: int = Field(..., description="Number of lines in original")
    new_start: int = Field(..., description="Starting line in new file")
    new_count: int = Field(..., description="Number of lines in new")
    content: str = Field(..., description="The diff content with +/- prefixes")
    context: str = Field(default="", description="Function or class context")


class CodeChange(BaseModel):
    """
    Single code change - language INFERRED from file extension and context.
    Outputs unified diff format for reviewability.
    """
    filepath: str = Field(
        ..., 
        description="Full path matching existing project structure"
    )
    action: str = Field(
        ..., 
        description="create, modify, or delete"
    )
    language: str = Field(
        ..., 
        description="INFERRED from file extension and existing code"
    )
    content: str = Field(
        ..., 
        min_length=20, 
        description="Complete file content (for create) or unified diff (for modify)"
    )
    unified_diff: Optional[str] = Field(
        default=None,
        description="Unified diff format for this change"
    )
    hunks: List[DiffHunk] = Field(
        default_factory=list,
        description="Parsed diff hunks for structured display"
    )
    purpose: str = Field(..., description="What this change accomplishes")
    implements_requirements: List[str] = Field(
        ..., 
        description="List of REQ-XXX IDs this implements"
    )
    follows_patterns_from: List[str] = Field(
        default_factory=list,
        description="Existing files whose patterns were followed"
    )
    additions: int = Field(default=0, description="Lines added")
    deletions: int = Field(default=0, description="Lines deleted")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        if v not in ['create', 'modify', 'delete']:
            raise ValueError('Action must be create, modify, or delete')
        return v
    
    def to_unified_diff(self) -> str:
        """Generate unified diff string for this change"""
        if self.unified_diff:
            return self.unified_diff
        
        # For new files, generate a diff from /dev/null
        if self.action == "create":
            lines = self.content.split('\n')
            diff_lines = [
                f"diff --git a/{self.filepath} b/{self.filepath}",
                "new file mode 100644",
                "index 0000000..1234567",
                f"--- /dev/null",
                f"+++ b/{self.filepath}",
                f"@@ -0,0 +1,{len(lines)} @@"
            ]
            for line in lines:
                diff_lines.append(f"+{line}")
            return '\n'.join(diff_lines)
        
        # For deletions
        if self.action == "delete":
            return f"diff --git a/{self.filepath} b/{self.filepath}\ndeleted file mode 100644"
        
        # For modifications, use the unified_diff if available
        return self.unified_diff or self.content


class CodeOutput(BaseModel):
    """
    STRICT output schema for CodeAgent.
    Language/framework INFERRED from repository context.
    """
    changes: List[CodeChange] = Field(..., min_length=1)
    languages_detected: List[str] = Field(
        ..., 
        description="Languages found in the repository"
    )
    frameworks_detected: List[str] = Field(
        default_factory=list,
        description="Frameworks/libraries detected in the repository"
    )
    integration_steps: List[str] = Field(
        ..., 
        description="Steps to integrate these changes"
    )
    dependencies_required: List[str] = Field(
        default_factory=list, 
        description="New dependencies if any - with justification"
    )
    patterns_followed: List[str] = Field(
        ..., 
        description="Existing patterns in the codebase that were followed"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made due to incomplete context"
    )

    # Backwards compatibility
    @property
    def files(self):
        """Backwards compatibility with old schema"""
        return self.changes


# ===========================================
# TEST AGENT SCHEMA (FRAMEWORK-INFERRED)
# ===========================================

class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"


class TestCase(BaseModel):
    """
    Single test case - framework INFERRED from existing tests.
    """
    name: str = Field(..., description="Test name following project conventions")
    description: str
    test_type: TestType
    target_file: str = Field(..., description="Which file/module this tests")
    covers_requirement: str = Field(..., description="REQ-XXX this test covers")
    code: str = Field(
        ..., 
        min_length=30, 
        description="Complete test code in the INFERRED framework"
    )
    assertions_count: int = Field(
        default=1,
        ge=0,
        description="Number of assertions in this test (0 if not countable)"
    )

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        # Minimal validation - just ensure it's not empty
        if len(v.strip()) < 30:
            raise ValueError('Test code must be at least 30 characters')
        return v


class TestOutput(BaseModel):
    """
    STRICT output schema for TestAgent.
    Framework INFERRED from existing tests or project conventions.
    """
    testing_framework: str = Field(
        ..., 
        description="INFERRED testing framework (pytest, jest, go test, etc.)"
    )
    framework_evidence: str = Field(
        ...,
        description="How the framework was inferred (existing files, config, etc.)"
    )
    tests: List[TestCase] = Field(..., min_length=1)
    test_file_path: str = Field(
        ..., 
        description="Where the test file should be placed (following project conventions)"
    )
    test_file_content: str = Field(
        ..., 
        description="Complete test file ready to run"
    )
    setup_instructions: List[str] = Field(
        ..., 
        description="How to run these tests"
    )
    coverage_analysis: str = Field(
        ..., 
        description="Which requirements are covered"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made (e.g., if no existing tests found)"
    )


# ===========================================
# AGENT FAILURE SCHEMA
# ===========================================

class AgentError(BaseModel):
    """Structured error when agent fails"""
    agent_name: str
    error_type: str
    message: str
    retry_possible: bool
    input_hash: str = Field(default="", description="Hash of input for debugging")
