"""
Requirement Analyzer Agent

This agent is responsible for analyzing Jira tickets and extracting
structured requirements including:
- Functional requirements
- Non-functional requirements
- Constraints
- Edge cases
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.logger import logger


class ExtractedRequirement(BaseModel):
    """Model for an extracted requirement"""
    id: str
    type: str = Field(description="functional, non-functional, or constraint")
    description: str
    priority: str = Field(default="medium", description="high, medium, or low")
    acceptance_criteria: Optional[List[str]] = None
    edge_cases: Optional[List[str]] = None


class RequirementAnalysisResult(BaseModel):
    """Result of requirement analysis"""
    ticket_id: str
    requirements: List[ExtractedRequirement]
    summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    raw_analysis: Optional[str] = None


class RequirementAgent:
    """
    Agent for analyzing and extracting requirements from Jira tickets.
    
    This agent uses LLM to:
    1. Parse ticket description and acceptance criteria
    2. Extract structured requirements
    3. Identify edge cases and constraints
    4. Prioritize requirements
    
    Example usage:
        agent = RequirementAgent()
        result = await agent.analyze(ticket_data)
    """
    
    def __init__(self, llm=None):
        """
        Initialize the Requirement Agent.
        
        Args:
            llm: Optional LLM instance. If not provided, will be created from config.
        """
        self.llm = llm
        self.name = "RequirementAnalyzer"
        logger.info(f"Initialized {self.name}")
    
    async def analyze(
        self,
        ticket_id: str,
        title: str,
        description: str,
        acceptance_criteria: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RequirementAnalysisResult:
        """
        Analyze a ticket and extract requirements.
        
        Args:
            ticket_id: The Jira ticket ID
            title: Ticket title
            description: Ticket description
            acceptance_criteria: Optional acceptance criteria text
            context: Optional additional context (e.g., from RAG)
        
        Returns:
            RequirementAnalysisResult with extracted requirements
        """
        logger.info(f"Analyzing ticket: {ticket_id}")
        
        # TODO: Implement actual LLM-based analysis
        # For now, return mock data to demonstrate the structure
        
        # This is where we'll add LangChain integration:
        # 1. Create a prompt template for requirement extraction
        # 2. Call the LLM with the ticket data
        # 3. Parse the structured output
        # 4. Return the results
        
        mock_requirements = [
            ExtractedRequirement(
                id=f"{ticket_id}-REQ-001",
                type="functional",
                description=f"Primary requirement from: {title}",
                priority="high",
                acceptance_criteria=["Requirement is implemented", "Tests pass"],
                edge_cases=["Handle empty input", "Handle special characters"]
            ),
            ExtractedRequirement(
                id=f"{ticket_id}-REQ-002",
                type="non-functional",
                description="System should respond within 3 seconds",
                priority="medium"
            )
        ]
        
        result = RequirementAnalysisResult(
            ticket_id=ticket_id,
            requirements=mock_requirements,
            summary=f"Extracted {len(mock_requirements)} requirements from ticket {ticket_id}",
            confidence_score=0.85
        )
        
        logger.info(f"Completed analysis for {ticket_id}: {len(mock_requirements)} requirements found")
        return result
    
    def _create_analysis_prompt(
        self,
        title: str,
        description: str,
        acceptance_criteria: Optional[str]
    ) -> str:
        """
        Create the prompt for requirement analysis.
        
        This will be used with LangChain's prompt templates.
        """
        prompt = f"""Analyze the following Jira ticket and extract structured requirements.

TICKET TITLE: {title}

DESCRIPTION:
{description}

"""
        if acceptance_criteria:
            prompt += f"""ACCEPTANCE CRITERIA:
{acceptance_criteria}

"""
        
        prompt += """Please extract and categorize requirements into:
1. Functional Requirements - What the system should do
2. Non-Functional Requirements - Performance, security, usability constraints
3. Constraints - Technical or business limitations
4. Edge Cases - Boundary conditions and error scenarios

For each requirement, provide:
- A unique ID
- Type (functional/non-functional/constraint)
- Clear description
- Priority (high/medium/low)
- Related acceptance criteria
- Potential edge cases

Return the results in a structured JSON format."""
        
        return prompt
    
    async def validate_requirements(
        self,
        requirements: List[ExtractedRequirement]
    ) -> Dict[str, Any]:
        """
        Validate extracted requirements for completeness and consistency.
        
        Args:
            requirements: List of extracted requirements
        
        Returns:
            Validation results with any issues found
        """
        issues = []
        warnings = []
        
        # Check for minimum requirements
        if len(requirements) == 0:
            issues.append("No requirements extracted")
        
        # Check for functional requirements
        functional = [r for r in requirements if r.type == "functional"]
        if len(functional) == 0:
            warnings.append("No functional requirements found")
        
        # Check for priorities
        high_priority = [r for r in requirements if r.priority == "high"]
        if len(high_priority) == 0:
            warnings.append("No high-priority requirements identified")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "stats": {
                "total": len(requirements),
                "functional": len(functional),
                "high_priority": len(high_priority)
            }
        }
