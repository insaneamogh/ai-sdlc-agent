"""
Requirement Agent Strategies

Standard and Strict strategy implementations for requirement extraction.
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


class ExtractedRequirement(BaseModel):
    """Model for an extracted requirement"""
    id: str
    type: str = Field(description="functional, non-functional, or constraint")
    description: str
    priority: str = Field(default="medium", description="high, medium, or low")
    source: Optional[str] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)


class RequirementOutput(AgentOutput):
    """Output from requirement analysis"""
    ticket_id: str
    functional_requirements: List[ExtractedRequirement] = Field(default_factory=list)
    non_functional_requirements: List[ExtractedRequirement] = Field(default_factory=list)
    constraints: List[ExtractedRequirement] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    summary: str = ""
    
    @property
    def all_requirements(self) -> List[ExtractedRequirement]:
        """Get all requirements combined"""
        return self.functional_requirements + self.non_functional_requirements + self.constraints


class StandardRequirementStrategy(AgentStrategy[RequirementOutput]):
    """
    Standard strategy for requirement extraction.
    
    Uses flexible JSON output parsing with fallback handling.
    Good for initial attempts where some flexibility is acceptable.
    """
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.STANDARD
    
    def get_system_prompt(self) -> str:
        return """You are an expert requirements analyst. Analyze the given ticket/repository information and extract structured requirements.

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{
  "functional_requirements": [
    {
      "id": "FR-001",
      "type": "functional",
      "description": "Clear requirement description",
      "priority": "high",
      "source": "ticket description",
      "acceptance_criteria": ["criterion 1", "criterion 2"],
      "edge_cases": ["edge case 1"]
    }
  ],
  "non_functional_requirements": [
    {
      "id": "NFR-001",
      "type": "non-functional",
      "description": "Performance or quality requirement",
      "priority": "medium"
    }
  ],
  "constraints": [
    {
      "id": "CON-001",
      "type": "constraint",
      "description": "Technical or business constraint",
      "priority": "high"
    }
  ],
  "edge_cases": ["Edge case 1", "Edge case 2"],
  "assumptions": ["Assumption 1", "Assumption 2"],
  "summary": "Brief summary of the analysis",
  "confidence_score": 0.85,
  "reasoning_steps": ["Step 1: Analyzed title", "Step 2: Extracted requirements"]
}

Types: functional, non-functional, constraint
Priorities: high, medium, low

Extract at least 3-5 meaningful requirements. Be thorough but concise."""
    
    def get_user_prompt(self, **kwargs) -> str:
        title = kwargs.get("title", "")
        description = kwargs.get("description", "")
        acceptance_criteria = kwargs.get("acceptance_criteria", "")
        
        prompt = f"""Analyze this and extract requirements:

TITLE: {title}

DESCRIPTION:
{description}
"""
        if acceptance_criteria:
            prompt += f"""
ACCEPTANCE CRITERIA:
{acceptance_criteria}
"""
        
        prompt += """
Extract comprehensive requirements including:
1. Functional requirements (what the system should do)
2. Non-functional requirements (performance, security, usability)
3. Constraints (technical or business limitations)
4. Edge cases to consider
5. Assumptions made"""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response, handling markdown code blocks"""
        text = response.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Find start and end of code block
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
            # Return empty structure on parse failure
            return {
                "functional_requirements": [],
                "non_functional_requirements": [],
                "constraints": [],
                "edge_cases": [],
                "assumptions": [],
                "summary": "Failed to parse response",
                "confidence_score": 0.0,
                "reasoning_steps": []
            }
    
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> RequirementOutput:
        """Create RequirementOutput from parsed data"""
        ticket_id = kwargs.get("ticket_id", "UNKNOWN")
        
        # Parse functional requirements
        functional = []
        for i, req in enumerate(parsed_data.get("functional_requirements", [])):
            functional.append(ExtractedRequirement(
                id=req.get("id", f"FR-{i+1:03d}"),
                type="functional",
                description=req.get("description", ""),
                priority=req.get("priority", "medium"),
                source=req.get("source"),
                acceptance_criteria=req.get("acceptance_criteria", []),
                edge_cases=req.get("edge_cases", [])
            ))
        
        # Parse non-functional requirements
        non_functional = []
        for i, req in enumerate(parsed_data.get("non_functional_requirements", [])):
            non_functional.append(ExtractedRequirement(
                id=req.get("id", f"NFR-{i+1:03d}"),
                type="non-functional",
                description=req.get("description", ""),
                priority=req.get("priority", "medium"),
                source=req.get("source"),
                acceptance_criteria=req.get("acceptance_criteria", []),
                edge_cases=req.get("edge_cases", [])
            ))
        
        # Parse constraints
        constraints = []
        for i, req in enumerate(parsed_data.get("constraints", [])):
            constraints.append(ExtractedRequirement(
                id=req.get("id", f"CON-{i+1:03d}"),
                type="constraint",
                description=req.get("description", ""),
                priority=req.get("priority", "medium"),
                source=req.get("source"),
                acceptance_criteria=req.get("acceptance_criteria", []),
                edge_cases=req.get("edge_cases", [])
            ))
        
        total_count = len(functional) + len(non_functional) + len(constraints)
        confidence = parsed_data.get("confidence_score", 0.8 if total_count > 0 else 0.0)
        
        return RequirementOutput(
            agent_name="RequirementAnalyzer",
            mode=self.mode,
            ticket_id=ticket_id,
            functional_requirements=functional,
            non_functional_requirements=non_functional,
            constraints=constraints,
            edge_cases=parsed_data.get("edge_cases", []),
            assumptions=parsed_data.get("assumptions", []),
            summary=parsed_data.get("summary", f"Extracted {total_count} requirements"),
            quality_metrics=QualityMetrics(
                confidence_score=confidence,
                completeness_score=min(1.0, total_count / 5),  # Target 5 requirements
                items_count=total_count,
                has_errors=total_count == 0
            ),
            reasoning_trace=ReasoningTrace(
                steps=parsed_data.get("reasoning_steps", [])
            )
        )


class StrictRequirementStrategy(AgentStrategy[RequirementOutput]):
    """
    Strict strategy for requirement extraction.
    
    Uses more explicit prompting and validation for higher quality output.
    Used when standard strategy doesn't meet quality thresholds.
    """
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.STRICT
    
    def get_system_prompt(self) -> str:
        return """You are a senior requirements analyst with 20 years of experience. Your task is to extract PRECISE, ACTIONABLE requirements from the given input.

CRITICAL RULES:
1. Every requirement MUST be testable and measurable
2. Every requirement MUST have clear acceptance criteria
3. Identify ALL edge cases - missing edge cases cause production bugs
4. Be explicit about assumptions - implicit assumptions cause scope creep
5. Prioritize based on business value and technical risk

Return ONLY valid JSON in this EXACT format:
{
  "functional_requirements": [
    {
      "id": "FR-001",
      "type": "functional",
      "description": "PRECISE description of what the system SHALL do",
      "priority": "high",
      "source": "exact source in input",
      "acceptance_criteria": [
        "GIVEN [precondition] WHEN [action] THEN [result]",
        "GIVEN [precondition] WHEN [action] THEN [result]"
      ],
      "edge_cases": [
        "What happens when [boundary condition]",
        "What happens when [error condition]"
      ]
    }
  ],
  "non_functional_requirements": [
    {
      "id": "NFR-001",
      "type": "non-functional",
      "description": "MEASURABLE quality attribute (e.g., 'Response time < 200ms')",
      "priority": "high",
      "acceptance_criteria": ["Specific measurement criteria"]
    }
  ],
  "constraints": [
    {
      "id": "CON-001",
      "type": "constraint",
      "description": "Technical or business limitation",
      "priority": "high"
    }
  ],
  "edge_cases": [
    "Null/empty input handling",
    "Boundary value handling",
    "Concurrent access handling",
    "Error state recovery"
  ],
  "assumptions": [
    "Explicit assumption with rationale"
  ],
  "summary": "Executive summary of requirements scope",
  "confidence_score": 0.95,
  "reasoning_steps": [
    "Step 1: Identified primary user story",
    "Step 2: Decomposed into functional requirements",
    "Step 3: Identified quality attributes",
    "Step 4: Analyzed edge cases",
    "Step 5: Documented assumptions"
  ]
}

MINIMUM REQUIREMENTS:
- At least 3 functional requirements
- At least 1 non-functional requirement
- At least 3 edge cases
- At least 2 acceptance criteria per functional requirement"""
    
    def get_user_prompt(self, **kwargs) -> str:
        title = kwargs.get("title", "")
        description = kwargs.get("description", "")
        acceptance_criteria = kwargs.get("acceptance_criteria", "")
        
        prompt = f"""STRICT ANALYSIS REQUIRED

Analyze this input with maximum rigor:

TITLE: {title}

DESCRIPTION:
{description}
"""
        if acceptance_criteria:
            prompt += f"""
EXISTING ACCEPTANCE CRITERIA:
{acceptance_criteria}
"""
        
        prompt += """
REQUIRED OUTPUT:
1. Extract ALL functional requirements (minimum 3)
2. Identify ALL non-functional requirements (performance, security, etc.)
3. Document ALL constraints
4. List ALL edge cases (minimum 3) - think about:
   - Null/empty inputs
   - Boundary values
   - Error conditions
   - Concurrent access
   - Data validation failures
5. State ALL assumptions explicitly

Be thorough. Missing requirements cause project failures."""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse with strict validation"""
        text = response.strip()
        
        # Remove markdown code blocks if present
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
            fr_count = len(data.get("functional_requirements", []))
            edge_count = len(data.get("edge_cases", []))
            
            if fr_count < 3:
                data["validation_warnings"] = data.get("validation_warnings", [])
                data["validation_warnings"].append(f"Only {fr_count} functional requirements (minimum 3)")
            
            if edge_count < 3:
                data["validation_warnings"] = data.get("validation_warnings", [])
                data["validation_warnings"].append(f"Only {edge_count} edge cases (minimum 3)")
            
            return data
            
        except json.JSONDecodeError:
            return {
                "functional_requirements": [],
                "non_functional_requirements": [],
                "constraints": [],
                "edge_cases": [],
                "assumptions": [],
                "summary": "Failed to parse strict response",
                "confidence_score": 0.0,
                "reasoning_steps": [],
                "validation_warnings": ["JSON parse failed"]
            }
    
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> RequirementOutput:
        """Create RequirementOutput with strict validation"""
        ticket_id = kwargs.get("ticket_id", "UNKNOWN")
        
        # Parse functional requirements with validation
        functional = []
        for i, req in enumerate(parsed_data.get("functional_requirements", [])):
            ac = req.get("acceptance_criteria", [])
            functional.append(ExtractedRequirement(
                id=req.get("id", f"FR-{i+1:03d}"),
                type="functional",
                description=req.get("description", ""),
                priority=req.get("priority", "medium"),
                source=req.get("source"),
                acceptance_criteria=ac,
                edge_cases=req.get("edge_cases", [])
            ))
        
        # Parse non-functional requirements
        non_functional = []
        for i, req in enumerate(parsed_data.get("non_functional_requirements", [])):
            non_functional.append(ExtractedRequirement(
                id=req.get("id", f"NFR-{i+1:03d}"),
                type="non-functional",
                description=req.get("description", ""),
                priority=req.get("priority", "medium"),
                source=req.get("source"),
                acceptance_criteria=req.get("acceptance_criteria", []),
                edge_cases=req.get("edge_cases", [])
            ))
        
        # Parse constraints
        constraints = []
        for i, req in enumerate(parsed_data.get("constraints", [])):
            constraints.append(ExtractedRequirement(
                id=req.get("id", f"CON-{i+1:03d}"),
                type="constraint",
                description=req.get("description", ""),
                priority=req.get("priority", "medium"),
                source=req.get("source"),
                acceptance_criteria=req.get("acceptance_criteria", []),
                edge_cases=req.get("edge_cases", [])
            ))
        
        total_count = len(functional) + len(non_functional) + len(constraints)
        edge_cases = parsed_data.get("edge_cases", [])
        
        # Calculate confidence based on completeness
        base_confidence = parsed_data.get("confidence_score", 0.9)
        
        # Penalize for missing minimums
        if len(functional) < 3:
            base_confidence -= 0.1
        if len(edge_cases) < 3:
            base_confidence -= 0.1
        
        # Check acceptance criteria coverage
        ac_coverage = sum(1 for f in functional if len(f.acceptance_criteria) >= 2) / max(len(functional), 1)
        base_confidence = base_confidence * (0.8 + 0.2 * ac_coverage)
        
        confidence = max(0.0, min(1.0, base_confidence))
        
        warnings = parsed_data.get("validation_warnings", [])
        
        return RequirementOutput(
            agent_name="RequirementAnalyzer",
            mode=self.mode,
            ticket_id=ticket_id,
            functional_requirements=functional,
            non_functional_requirements=non_functional,
            constraints=constraints,
            edge_cases=edge_cases,
            assumptions=parsed_data.get("assumptions", []),
            summary=parsed_data.get("summary", f"Extracted {total_count} requirements (strict mode)"),
            quality_metrics=QualityMetrics(
                confidence_score=confidence,
                completeness_score=min(1.0, (total_count + len(edge_cases)) / 8),
                items_count=total_count,
                has_errors=len(warnings) > 0,
                error_messages=warnings
            ),
            reasoning_trace=ReasoningTrace(
                steps=parsed_data.get("reasoning_steps", []),
                decisions_made=[{"mode": "strict", "reason": "Quality gate enforcement"}]
            )
        )
