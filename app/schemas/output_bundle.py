"""
Enterprise Output Bundle Schema

This module defines the comprehensive output bundle that aggregates
all pipeline artifacts into a single, reviewable engineering artifact.

The bundle contains:
- Requirements Specification
- Code Diff with metadata
- Test Suite with coverage
- Execution Summary with decisions
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class BundleStatus(str, Enum):
    """Status of the output bundle"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class QualityGateResult(BaseModel):
    """Result of a quality gate check"""
    gate_name: str
    passed: bool
    threshold: float
    actual_value: float
    message: str = ""


class WorkflowDecision(BaseModel):
    """A decision made during workflow execution"""
    node: str
    decision: str
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionSummary(BaseModel):
    """Summary of workflow execution"""
    workflow_id: str
    thread_id: str
    ticket_id: str
    action: str
    agents_executed: List[str] = Field(default_factory=list)
    decisions: List[WorkflowDecision] = Field(default_factory=list)
    quality_gates: List[QualityGateResult] = Field(default_factory=list)
    execution_time_ms: int = 0
    started_at: str = ""
    completed_at: str = ""
    retries: int = 0
    final_status: BundleStatus = BundleStatus.SUCCESS
    errors: List[str] = Field(default_factory=list)


class RequirementItem(BaseModel):
    """A single requirement in the spec"""
    id: str
    type: str
    description: str
    priority: str = "medium"
    source: Optional[str] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)


class RequirementsSpec(BaseModel):
    """Requirements specification artifact"""
    functional_requirements: List[RequirementItem] = Field(default_factory=list)
    non_functional_requirements: List[RequirementItem] = Field(default_factory=list)
    constraints: List[RequirementItem] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def total_requirements(self) -> int:
        return len(self.functional_requirements) + len(self.non_functional_requirements) + len(self.constraints)
    
    def to_markdown(self) -> str:
        """Export as Markdown"""
        lines = ["# Requirements Specification\n"]
        
        if self.functional_requirements:
            lines.append("## Functional Requirements\n")
            for req in self.functional_requirements:
                lines.append(f"### {req.id}: {req.description}\n")
                lines.append(f"- **Priority:** {req.priority}")
                if req.source:
                    lines.append(f"- **Source:** {req.source}")
                if req.acceptance_criteria:
                    lines.append("\n**Acceptance Criteria:**")
                    for ac in req.acceptance_criteria:
                        lines.append(f"- {ac}")
                if req.edge_cases:
                    lines.append("\n**Edge Cases:**")
                    for ec in req.edge_cases:
                        lines.append(f"- {ec}")
                lines.append("")
        
        if self.non_functional_requirements:
            lines.append("## Non-Functional Requirements\n")
            for req in self.non_functional_requirements:
                lines.append(f"- **{req.id}:** {req.description} (Priority: {req.priority})")
        
        if self.constraints:
            lines.append("\n## Constraints\n")
            for req in self.constraints:
                lines.append(f"- **{req.id}:** {req.description}")
        
        if self.edge_cases:
            lines.append("\n## Edge Cases\n")
            for ec in self.edge_cases:
                lines.append(f"- {ec}")
        
        if self.assumptions:
            lines.append("\n## Assumptions\n")
            for a in self.assumptions:
                lines.append(f"- {a}")
        
        return "\n".join(lines)


class DiffHunk(BaseModel):
    """A single diff hunk"""
    file: str
    old_start: int = 1
    old_count: int = 0
    new_start: int = 1
    new_count: int = 0
    content: str
    description: str = ""


class ImpactAnalysis(BaseModel):
    """Analysis of code change impact"""
    affected_classes: List[str] = Field(default_factory=list)
    affected_methods: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    breaking_change_risk: str = "low"
    migration_notes: List[str] = Field(default_factory=list)


class CodeDiff(BaseModel):
    """Code diff artifact with metadata"""
    format: str = "unified_diff"
    files_modified: List[str] = Field(default_factory=list)
    hunks: List[DiffHunk] = Field(default_factory=list)
    unified_diff: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reasoning_trace: List[str] = Field(default_factory=list)
    rag_sources_used: List[str] = Field(default_factory=list)
    patterns_applied: List[str] = Field(default_factory=list)
    impact_analysis: ImpactAnalysis = Field(default_factory=ImpactAnalysis)
    confidence: float = 0.0
    
    def get_full_diff(self) -> str:
        """Get the complete unified diff"""
        if self.unified_diff:
            return self.unified_diff
        
        diff_parts = []
        for hunk in self.hunks:
            diff_parts.append(f"diff --git a/{hunk.file} b/{hunk.file}")
            diff_parts.append(f"--- a/{hunk.file}")
            diff_parts.append(f"+++ b/{hunk.file}")
            diff_parts.append(f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@")
            diff_parts.append(hunk.content)
        
        return "\n".join(diff_parts)
    
    def to_patch_file(self) -> str:
        """Export as patch file content"""
        return self.get_full_diff()


class TestItem(BaseModel):
    """A single test in the suite"""
    name: str
    description: str
    test_type: str = "unit"
    code: str
    covers_requirement: Optional[str] = None
    covers_method: Optional[str] = None
    assertions: int = 0
    status: str = "pending"


class CoverageMetrics(BaseModel):
    """Test coverage metrics"""
    method_coverage: float = 0.0
    branch_coverage: float = 0.0
    line_coverage: float = 0.0
    assertion_density: float = 0.0
    edge_case_coverage: float = 0.0


class TestSuite(BaseModel):
    """Test suite artifact"""
    framework: str = "pytest"
    tests: List[TestItem] = Field(default_factory=list)
    test_file: str = ""
    target_files: List[str] = Field(default_factory=list)
    coverage_metrics: CoverageMetrics = Field(default_factory=CoverageMetrics)
    covered_requirements: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    
    @property
    def total_tests(self) -> int:
        return len(self.tests)
    
    @property
    def total_assertions(self) -> int:
        return sum(t.assertions for t in self.tests)
    
    def to_test_file(self) -> str:
        """Export as test file content"""
        if self.test_file:
            return self.test_file
        
        header = f'''"""
Generated Test Suite

Framework: {self.framework}
Tests: {self.total_tests}
Assertions: {self.total_assertions}
"""

import pytest


'''
        return header + "\n\n".join(t.code for t in self.tests)


class OutputBundle(BaseModel):
    """
    Enterprise Output Bundle
    
    The complete artifact bundle returned by the SDLC pipeline.
    Contains all reviewable engineering artifacts:
    - Requirements Specification
    - Code Diff with metadata
    - Test Suite with coverage
    - Execution Summary with decisions
    
    This is what the user actually receives - not chat text.
    """
    bundle_id: str
    ticket_id: str
    thread_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Artifacts
    requirements_spec: Optional[RequirementsSpec] = None
    code_diff: Optional[CodeDiff] = None
    test_suite: Optional[TestSuite] = None
    
    # Execution metadata
    execution_summary: ExecutionSummary
    
    # Overall quality
    overall_confidence: float = 0.0
    quality_gates_passed: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "bundle_id": "run-2026-01-16-001",
                "ticket_id": "JIRA-124",
                "thread_id": "abc-123-def-456",
                "created_at": "2026-01-16T10:30:00Z",
                "requirements_spec": {
                    "functional_requirements": [
                        {
                            "id": "FR-001",
                            "type": "functional",
                            "description": "Calculate tax based on user income slab",
                            "priority": "high",
                            "source": "JIRA-124 description",
                            "acceptance_criteria": [
                                "GIVEN income <= 250000 WHEN calculate_tax THEN return 0",
                                "GIVEN income > 250000 WHEN calculate_tax THEN return correct tax"
                            ],
                            "edge_cases": ["Negative income", "Null input"]
                        }
                    ],
                    "non_functional_requirements": [
                        {
                            "id": "NFR-001",
                            "type": "non-functional",
                            "description": "Response time < 200ms",
                            "priority": "medium"
                        }
                    ],
                    "edge_cases": ["Negative income values", "Null income input"],
                    "assumptions": ["Currency is INR", "Tax slabs are configurable"]
                },
                "code_diff": {
                    "format": "unified_diff",
                    "files_modified": ["tax.py"],
                    "hunks": [
                        {
                            "file": "tax.py",
                            "old_start": 1,
                            "new_start": 1,
                            "new_count": 12,
                            "content": "+def calculate_tax(income: float) -> float:..."
                        }
                    ],
                    "reasoning_trace": [
                        "Matched existing tax calculation pattern",
                        "Followed repository error-handling style"
                    ],
                    "rag_sources_used": ["PR-456", "tax_utils.py"],
                    "confidence": 0.88
                },
                "test_suite": {
                    "framework": "pytest",
                    "tests": [
                        {
                            "name": "test_zero_income",
                            "description": "Test zero income returns zero tax",
                            "test_type": "unit",
                            "code": "def test_zero_income():\n    assert calculate_tax(0) == 0.0",
                            "covers_requirement": "FR-001",
                            "assertions": 1
                        }
                    ],
                    "coverage_metrics": {
                        "method_coverage": 100.0,
                        "branch_coverage": 85.0,
                        "line_coverage": 90.0
                    },
                    "confidence": 0.90
                },
                "execution_summary": {
                    "workflow_id": "run-2026-01-16-001",
                    "thread_id": "abc-123-def-456",
                    "ticket_id": "JIRA-124",
                    "action": "full_pipeline",
                    "agents_executed": ["requirement_analyzer", "code_generator", "test_generator"],
                    "decisions": [
                        {
                            "node": "requirement_analyzer",
                            "decision": "proceed",
                            "reason": "confidence 0.92 >= 0.7"
                        }
                    ],
                    "execution_time_ms": 18420,
                    "quality_gates_passed": True
                },
                "overall_confidence": 0.90,
                "quality_gates_passed": True
            }
        }
    
    def to_json(self) -> str:
        """Export as JSON string"""
        return self.model_dump_json(indent=2)
    
    def to_file_bundle(self) -> Dict[str, str]:
        """
        Export as file bundle dictionary.
        
        Returns:
            Dict mapping filename to content:
            - requirements.json
            - patch.diff
            - test_suite.py
            - execution_summary.json
        """
        files = {}
        
        if self.requirements_spec:
            files["requirements.json"] = self.requirements_spec.model_dump_json(indent=2)
            files["requirements.md"] = self.requirements_spec.to_markdown()
        
        if self.code_diff:
            files["patch.diff"] = self.code_diff.to_patch_file()
            files["code_metadata.json"] = self.code_diff.model_dump_json(indent=2, exclude={"unified_diff"})
        
        if self.test_suite:
            files["test_suite.py"] = self.test_suite.to_test_file()
            files["test_metadata.json"] = self.test_suite.model_dump_json(indent=2, exclude={"test_file"})
        
        files["execution_summary.json"] = self.execution_summary.model_dump_json(indent=2)
        files["bundle.json"] = self.to_json()
        
        return files
    
    @classmethod
    def from_pipeline_state(
        cls,
        state: Dict[str, Any],
        thread_id: str,
        execution_time_ms: int = 0
    ) -> "OutputBundle":
        """
        Create OutputBundle from pipeline state.
        
        Args:
            state: Final state from LangGraph pipeline
            thread_id: Thread ID for the execution
            execution_time_ms: Total execution time
        
        Returns:
            OutputBundle with all artifacts
        """
        import uuid
        
        bundle_id = f"run-{datetime.utcnow().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
        ticket_id = state.get("ticket_id", "UNKNOWN")
        
        # Build requirements spec
        requirements_spec = None
        if state.get("requirements"):
            reqs = state["requirements"]
            requirements_spec = RequirementsSpec(
                functional_requirements=[
                    RequirementItem(**r) for r in reqs 
                    if r.get("type") == "functional"
                ],
                non_functional_requirements=[
                    RequirementItem(**r) for r in reqs 
                    if r.get("type") == "non-functional"
                ],
                constraints=[
                    RequirementItem(**r) for r in reqs 
                    if r.get("type") == "constraint"
                ],
                extraction_metadata={
                    "source": ticket_id,
                    "agent_results": [
                        r for r in state.get("agent_results", [])
                        if r.get("agent") == "RequirementAnalyzer"
                    ]
                }
            )
        
        # Build code diff
        code_diff = None
        if state.get("generated_code"):
            code_agent_result = next(
                (r for r in state.get("agent_results", []) if r.get("agent") == "CodeGenerator"),
                {}
            )
            code_diff = CodeDiff(
                files_modified=code_agent_result.get("result", {}).get("files_generated", []),
                unified_diff=state["generated_code"],
                patterns_applied=code_agent_result.get("result", {}).get("patterns_used", []),
                confidence=code_agent_result.get("result", {}).get("confidence", 0.0)
            )
        
        # Build test suite
        test_suite = None
        if state.get("generated_tests"):
            test_agent_result = next(
                (r for r in state.get("agent_results", []) if r.get("agent") == "TestGenerator"),
                {}
            )
            test_suite = TestSuite(
                test_file=state["generated_tests"],
                coverage_metrics=CoverageMetrics(
                    method_coverage=test_agent_result.get("result", {}).get("coverage_estimate", 0.0)
                ),
                confidence=test_agent_result.get("result", {}).get("confidence", 0.0)
            )
        
        # Build execution summary
        decisions = []
        for result in state.get("agent_results", []):
            decisions.append(WorkflowDecision(
                node=result.get("agent", "unknown"),
                decision="completed" if result.get("status") == "completed" else "failed",
                reason=f"Status: {result.get('status')}",
                timestamp=result.get("timestamp", ""),
                metadata=result.get("result", {})
            ))
        
        execution_summary = ExecutionSummary(
            workflow_id=bundle_id,
            thread_id=thread_id,
            ticket_id=ticket_id,
            action=state.get("action", "unknown"),
            agents_executed=[r.get("agent") for r in state.get("agent_results", [])],
            decisions=decisions,
            execution_time_ms=execution_time_ms,
            started_at=state.get("started_at", ""),
            completed_at=state.get("completed_at", ""),
            errors=state.get("errors", []),
            final_status=BundleStatus.SUCCESS if not state.get("errors") else BundleStatus.PARTIAL
        )
        
        # Calculate overall confidence
        confidences = []
        if requirements_spec:
            req_conf = next(
                (r.get("result", {}).get("confidence", 0) for r in state.get("agent_results", [])
                 if r.get("agent") == "RequirementAnalyzer"),
                0
            )
            confidences.append(req_conf)
        if code_diff:
            confidences.append(code_diff.confidence)
        if test_suite:
            confidences.append(test_suite.confidence)
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return cls(
            bundle_id=bundle_id,
            ticket_id=ticket_id,
            thread_id=thread_id,
            requirements_spec=requirements_spec,
            code_diff=code_diff,
            test_suite=test_suite,
            execution_summary=execution_summary,
            overall_confidence=overall_confidence,
            quality_gates_passed=not state.get("errors")
        )
