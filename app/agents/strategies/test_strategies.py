"""
Test Generator Agent Strategies

Standard and Strict strategy implementations for test generation.
Produces comprehensive test suites with coverage tracking.
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.agents.base import (
    AgentStrategy,
    AgentOutput,
    AgentMode,
    QualityMetrics,
    ReasoningTrace
)


class GeneratedTest(BaseModel):
    """Model for a generated test"""
    name: str
    description: str
    test_type: str = Field(default="unit", description="unit, integration, e2e, boundary")
    code: str
    covers_requirement: Optional[str] = None
    covers_method: Optional[str] = None
    assertions: int = 0
    covered_lines: List[int] = Field(default_factory=list)


class CoverageMetrics(BaseModel):
    """Test coverage metrics"""
    method_coverage: float = Field(default=0.0, ge=0.0, le=100.0)
    branch_coverage: float = Field(default=0.0, ge=0.0, le=100.0)
    line_coverage: float = Field(default=0.0, ge=0.0, le=100.0)
    assertion_density: float = Field(default=0.0, ge=0.0, le=100.0)
    edge_case_coverage: float = Field(default=0.0, ge=0.0, le=100.0)


class TestOutput(AgentOutput):
    """Output from test generation"""
    ticket_id: str
    tests: List[GeneratedTest] = Field(default_factory=list)
    test_file: str = ""
    test_framework: str = "pytest"
    target_files: List[str] = Field(default_factory=list)
    coverage_metrics: CoverageMetrics = Field(default_factory=CoverageMetrics)
    covered_requirements: List[str] = Field(default_factory=list)
    summary: str = ""
    
    @property
    def total_assertions(self) -> int:
        """Get total assertion count"""
        return sum(t.assertions for t in self.tests)
    
    @property
    def tests_by_type(self) -> Dict[str, List[GeneratedTest]]:
        """Group tests by type"""
        result = {}
        for test in self.tests:
            if test.test_type not in result:
                result[test.test_type] = []
            result[test.test_type].append(test)
        return result


class StandardTestStrategy(AgentStrategy[TestOutput]):
    """
    Standard strategy for test generation.
    
    Produces comprehensive test suites with coverage tracking.
    """
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.STANDARD
    
    def get_system_prompt(self) -> str:
        return """You are an expert test engineer. Generate comprehensive test cases for the given code.

Return ONLY valid JSON in this exact format:
{
  "tests": [
    {
      "name": "test_function_name_scenario",
      "description": "What this test verifies",
      "test_type": "unit",
      "code": "def test_function_name_scenario():\\n    # Arrange\\n    ...\\n    # Act\\n    ...\\n    # Assert\\n    assert result == expected",
      "covers_requirement": "FR-001",
      "covers_method": "function_name",
      "assertions": 2,
      "covered_lines": [10, 11, 12, 15]
    }
  ],
  "test_file": "Complete pytest file with all tests, imports, fixtures...",
  "test_framework": "pytest",
  "target_files": ["module.py"],
  "coverage_metrics": {
    "method_coverage": 85.0,
    "branch_coverage": 70.0,
    "line_coverage": 80.0,
    "assertion_density": 60.0,
    "edge_case_coverage": 75.0
  },
  "covered_requirements": ["FR-001", "FR-002"],
  "summary": "Brief summary of test coverage",
  "confidence_score": 0.85,
  "reasoning_trace": [
    "Identified testable methods",
    "Created happy path tests",
    "Added edge case tests"
  ],
  "patterns_matched": ["existing_test_pattern.py"]
}

test_type options: unit, integration, e2e, boundary

Generate tests that:
- Follow AAA pattern (Arrange, Act, Assert)
- Cover happy paths and edge cases
- Include meaningful assertions
- Match existing test patterns"""
    
    def get_user_prompt(self, **kwargs) -> str:
        code = kwargs.get("code", "")
        requirements = kwargs.get("requirements", [])
        test_framework = kwargs.get("test_framework", "pytest")
        
        req_text = "\n".join([
            f"- [{r.get('id', 'REQ')}] {r.get('description', 'Requirement')}" 
            for r in requirements
        ]) if requirements else "No specific requirements"
        
        prompt = f"""Generate {test_framework} tests for this code:

CODE TO TEST:
{code[:4000] if code else 'No code provided'}

REQUIREMENTS TO COVER:
{req_text}

Generate comprehensive tests including:
1. Happy path tests for main functionality
2. Edge case tests (null, empty, boundary values)
3. Error handling tests
4. Integration tests if applicable

Each test should have clear assertions and follow the AAA pattern."""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response"""
        text = response.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            start_idx = 1 if lines[0].startswith("```") else 0
            end_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            text = "\n".join(lines[start_idx:end_idx])
            if text.startswith("json"):
                text = text[4:].strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "tests": [],
                "test_file": "",
                "test_framework": "pytest",
                "target_files": [],
                "coverage_metrics": {},
                "covered_requirements": [],
                "summary": "Failed to parse response",
                "confidence_score": 0.0,
                "reasoning_trace": [],
                "patterns_matched": []
            }
    
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> TestOutput:
        """Create TestOutput from parsed data"""
        ticket_id = kwargs.get("ticket_id", "UNKNOWN")
        
        # Parse tests
        tests = []
        for t in parsed_data.get("tests", []):
            tests.append(GeneratedTest(
                name=t.get("name", "test_unnamed"),
                description=t.get("description", ""),
                test_type=t.get("test_type", "unit"),
                code=t.get("code", ""),
                covers_requirement=t.get("covers_requirement"),
                covers_method=t.get("covers_method"),
                assertions=t.get("assertions", 0),
                covered_lines=t.get("covered_lines", [])
            ))
        
        # Parse coverage metrics
        cov_data = parsed_data.get("coverage_metrics", {})
        coverage = CoverageMetrics(
            method_coverage=cov_data.get("method_coverage", 0.0),
            branch_coverage=cov_data.get("branch_coverage", 0.0),
            line_coverage=cov_data.get("line_coverage", 0.0),
            assertion_density=cov_data.get("assertion_density", 0.0),
            edge_case_coverage=cov_data.get("edge_case_coverage", 0.0)
        )
        
        test_count = len(tests)
        confidence = parsed_data.get("confidence_score", 0.8 if test_count > 0 else 0.0)
        
        return TestOutput(
            agent_name="TestGenerator",
            mode=self.mode,
            ticket_id=ticket_id,
            tests=tests,
            test_file=parsed_data.get("test_file", self._combine_tests(tests)),
            test_framework=parsed_data.get("test_framework", "pytest"),
            target_files=parsed_data.get("target_files", []),
            coverage_metrics=coverage,
            covered_requirements=parsed_data.get("covered_requirements", []),
            summary=parsed_data.get("summary", f"Generated {test_count} tests"),
            quality_metrics=QualityMetrics(
                confidence_score=confidence,
                completeness_score=min(1.0, test_count / 5),
                items_count=test_count,
                has_errors=test_count == 0
            ),
            reasoning_trace=ReasoningTrace(
                steps=parsed_data.get("reasoning_trace", []),
                patterns_matched=parsed_data.get("patterns_matched", [])
            )
        )
    
    def _combine_tests(self, tests: List[GeneratedTest]) -> str:
        """Combine tests into a single file"""
        header = '''"""
Generated Test Suite

Auto-generated tests for the implementation.
"""

import pytest


'''
        return header + "\n\n".join(t.code for t in tests)


class StrictTestStrategy(AgentStrategy[TestOutput]):
    """
    Strict strategy for test generation.
    
    Enforces comprehensive coverage with minimum thresholds.
    """
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.STRICT
    
    def get_system_prompt(self) -> str:
        return """You are a senior QA architect with 20 years of experience. Generate PRODUCTION-READY test suites that ensure code quality.

CRITICAL REQUIREMENTS:
1. Every public method MUST have at least one test
2. Every requirement MUST have traceability to tests
3. Edge cases MUST be explicitly tested
4. Error conditions MUST be tested
5. Tests MUST follow AAA pattern (Arrange, Act, Assert)

Return ONLY valid JSON in this EXACT format:
{
  "tests": [
    {
      "name": "test_calculate_tax_zero_income",
      "description": "Verify tax calculation returns 0 for zero income",
      "test_type": "unit",
      "code": "def test_calculate_tax_zero_income():\\n    '''Test zero income returns zero tax'''\\n    # Arrange\\n    income = 0\\n    \\n    # Act\\n    result = calculate_tax(income)\\n    \\n    # Assert\\n    assert result == 0.0\\n    assert isinstance(result, float)",
      "covers_requirement": "FR-001",
      "covers_method": "calculate_tax",
      "assertions": 2,
      "covered_lines": [5, 6, 7]
    },
    {
      "name": "test_calculate_tax_negative_income_raises",
      "description": "Verify negative income raises ValueError",
      "test_type": "boundary",
      "code": "def test_calculate_tax_negative_income_raises():\\n    '''Test negative income raises ValueError'''\\n    # Arrange\\n    income = -100\\n    \\n    # Act & Assert\\n    with pytest.raises(ValueError) as exc_info:\\n        calculate_tax(income)\\n    \\n    assert 'Invalid income' in str(exc_info.value)",
      "covers_requirement": "FR-001",
      "covers_method": "calculate_tax",
      "assertions": 1,
      "covered_lines": [8, 9]
    }
  ],
  "test_file": "Complete pytest file with imports, fixtures, all tests...",
  "test_framework": "pytest",
  "target_files": ["tax_calculator.py"],
  "coverage_metrics": {
    "method_coverage": 100.0,
    "branch_coverage": 85.0,
    "line_coverage": 90.0,
    "assertion_density": 75.0,
    "edge_case_coverage": 80.0
  },
  "covered_requirements": ["FR-001", "FR-002", "NFR-001"],
  "summary": "Comprehensive test suite with 100% method coverage",
  "confidence_score": 0.92,
  "reasoning_trace": [
    "Step 1: Identified all public methods",
    "Step 2: Created happy path tests for each method",
    "Step 3: Added boundary value tests",
    "Step 4: Added error condition tests",
    "Step 5: Verified requirement traceability"
  ],
  "patterns_matched": ["existing_test_style.py"]
}

MINIMUM REQUIREMENTS:
- At least 4 tests
- At least 1 boundary/edge case test
- At least 1 error handling test
- Method coverage >= 80%
- Each test must have at least 1 assertion"""
    
    def get_user_prompt(self, **kwargs) -> str:
        code = kwargs.get("code", "")
        requirements = kwargs.get("requirements", [])
        test_framework = kwargs.get("test_framework", "pytest")
        
        req_text = "\n".join([
            f"- [{r.get('id', 'REQ')}] {r.get('description', 'Requirement')}" 
            for r in requirements
        ]) if requirements else "No specific requirements"
        
        prompt = f"""STRICT TEST GENERATION REQUIRED

Generate comprehensive {test_framework} tests for:

CODE TO TEST:
{code[:4000] if code else 'No code provided'}

REQUIREMENTS TO COVER:
{req_text}

MANDATORY TEST CATEGORIES:
1. Happy path tests (minimum 2)
2. Boundary value tests (minimum 1)
   - Zero values
   - Maximum values
   - Boundary conditions
3. Error handling tests (minimum 1)
   - Invalid inputs
   - Exception scenarios
4. Edge case tests
   - Null/None handling
   - Empty collections
   - Special characters

EACH TEST MUST:
- Follow AAA pattern
- Have descriptive name
- Have docstring
- Have at least 1 assertion
- Link to requirement if applicable

Target: 80%+ method coverage"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse with strict validation"""
        text = response.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            start_idx = 1 if lines[0].startswith("```") else 0
            end_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            text = "\n".join(lines[start_idx:end_idx])
            if text.startswith("json"):
                text = text[4:].strip()
        
        try:
            data = json.loads(text)
            
            # Validate minimum requirements
            tests = data.get("tests", [])
            test_count = len(tests)
            boundary_tests = sum(1 for t in tests if t.get("test_type") in ["boundary", "edge"])
            error_tests = sum(1 for t in tests if "error" in t.get("name", "").lower() or "raises" in t.get("name", "").lower())
            
            warnings = []
            if test_count < 4:
                warnings.append(f"Only {test_count} tests (minimum 4)")
            if boundary_tests < 1:
                warnings.append("No boundary/edge case tests")
            if error_tests < 1:
                warnings.append("No error handling tests")
            
            # Check coverage
            cov = data.get("coverage_metrics", {})
            method_cov = cov.get("method_coverage", 0)
            if method_cov < 80:
                warnings.append(f"Method coverage {method_cov}% < 80%")
            
            data["validation_warnings"] = warnings
            return data
            
        except json.JSONDecodeError:
            return {
                "tests": [],
                "test_file": "",
                "test_framework": "pytest",
                "target_files": [],
                "coverage_metrics": {},
                "covered_requirements": [],
                "summary": "Failed to parse strict response",
                "confidence_score": 0.0,
                "reasoning_trace": [],
                "patterns_matched": [],
                "validation_warnings": ["JSON parse failed"]
            }
    
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> TestOutput:
        """Create TestOutput with strict validation"""
        ticket_id = kwargs.get("ticket_id", "UNKNOWN")
        
        # Parse tests
        tests = []
        for t in parsed_data.get("tests", []):
            tests.append(GeneratedTest(
                name=t.get("name", "test_unnamed"),
                description=t.get("description", ""),
                test_type=t.get("test_type", "unit"),
                code=t.get("code", ""),
                covers_requirement=t.get("covers_requirement"),
                covers_method=t.get("covers_method"),
                assertions=t.get("assertions", 0),
                covered_lines=t.get("covered_lines", [])
            ))
        
        # Parse coverage metrics
        cov_data = parsed_data.get("coverage_metrics", {})
        coverage = CoverageMetrics(
            method_coverage=cov_data.get("method_coverage", 0.0),
            branch_coverage=cov_data.get("branch_coverage", 0.0),
            line_coverage=cov_data.get("line_coverage", 0.0),
            assertion_density=cov_data.get("assertion_density", 0.0),
            edge_case_coverage=cov_data.get("edge_case_coverage", 0.0)
        )
        
        test_count = len(tests)
        warnings = parsed_data.get("validation_warnings", [])
        
        # Calculate confidence
        base_confidence = parsed_data.get("confidence_score", 0.9)
        if test_count < 4:
            base_confidence -= 0.1
        if len(warnings) > 0:
            base_confidence -= 0.05 * len(warnings)
        
        confidence = max(0.0, min(1.0, base_confidence))
        
        return TestOutput(
            agent_name="TestGenerator",
            mode=self.mode,
            ticket_id=ticket_id,
            tests=tests,
            test_file=parsed_data.get("test_file", self._combine_tests(tests)),
            test_framework=parsed_data.get("test_framework", "pytest"),
            target_files=parsed_data.get("target_files", []),
            coverage_metrics=coverage,
            covered_requirements=parsed_data.get("covered_requirements", []),
            summary=parsed_data.get("summary", f"Generated {test_count} tests (strict mode)"),
            quality_metrics=QualityMetrics(
                confidence_score=confidence,
                completeness_score=min(1.0, test_count / 6),
                items_count=test_count,
                has_errors=len(warnings) > 0,
                error_messages=warnings
            ),
            reasoning_trace=ReasoningTrace(
                steps=parsed_data.get("reasoning_trace", []),
                patterns_matched=parsed_data.get("patterns_matched", []),
                decisions_made=[{"mode": "strict", "reason": "Quality gate enforcement"}]
            )
        )
    
    def _combine_tests(self, tests: List[GeneratedTest]) -> str:
        """Combine tests into a single file"""
        header = '''"""
Generated Test Suite (Strict Mode)

Comprehensive test coverage with quality gates.
"""

import pytest


'''
        return header + "\n\n".join(t.code for t in tests)
