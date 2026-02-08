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
    fallback_used: bool = False


class RequirementAgent:
    """
    Agent for analyzing and extracting requirements from Jira tickets.
    
    This agent uses LLM to:
    1. Parse ticket description and acceptance criteria
    2. Extract structured requirements
    3. Identify edge cases and constraints
    4. Prioritize requirements
    
    Example usage:
        agent = RequirementAgent(model="gpt-4o")
        result = await agent.analyze(ticket_data)
    """
    
    def __init__(self, llm=None, model: str = None):
        """
        Initialize the Requirement Agent.
        
        Args:
            llm: Optional LLM instance. If not provided, will be created from config.
            model: Optional model name to use. If not provided, uses config default.
        """
        self.llm = llm
        self.model = model  # Store model override
        self.name = "RequirementAnalyzer"
        logger.info(f"Initialized {self.name} with model={model or 'default'}")
    
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
        
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            from app.config import get_settings
            import json
            
            settings = get_settings()
            
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            # Use model override if provided, otherwise use config default
            model_to_use = self.model or settings.openai_model
            logger.info(f"Using model: {model_to_use}")
            
            llm = ChatOpenAI(
                model=model_to_use,
                api_key=settings.openai_api_key,
                temperature=0.3
            )
            
            system_prompt = """You are an expert requirements analyst. Analyze the given ticket/repository information and extract structured requirements.

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{
  "requirements": [
    {
      "id": "REQ-001",
      "type": "functional",
      "description": "Clear requirement description",
      "priority": "high",
      "acceptance_criteria": ["criterion 1", "criterion 2"],
      "edge_cases": ["edge case 1"]
    }
  ],
  "summary": "Brief summary of analysis",
  "confidence_score": 0.85
}

Types: functional, non-functional, constraint
Priorities: high, medium, low"""

            user_prompt = f"""Analyze this and extract requirements:

TITLE: {title}

DESCRIPTION:
{description}

{f'ACCEPTANCE CRITERIA: {acceptance_criteria}' if acceptance_criteria else ''}

Extract at least 3-5 meaningful requirements based on the content."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await llm.ainvoke(messages)
            response_text = response.content.strip()
            
            # Clean up response if it has markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            parsed = json.loads(response_text)
            
            requirements = []
            for i, req in enumerate(parsed.get("requirements", [])):
                requirements.append(ExtractedRequirement(
                    id=req.get("id", f"{ticket_id}-REQ-{i+1:03d}"),
                    type=req.get("type", "functional"),
                    description=req.get("description", ""),
                    priority=req.get("priority", "medium"),
                    acceptance_criteria=req.get("acceptance_criteria"),
                    edge_cases=req.get("edge_cases")
                ))
            
            result = RequirementAnalysisResult(
                ticket_id=ticket_id,
                requirements=requirements,
                summary=parsed.get("summary", f"Extracted {len(requirements)} requirements"),
                confidence_score=parsed.get("confidence_score", 0.8),
                raw_analysis=response_text,
                fallback_used=False
            )
            
            logger.info(f"Completed analysis for {ticket_id}: {len(requirements)} requirements found")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}, falling back to mock data")
            # Fallback to mock data on error
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
            
            return RequirementAnalysisResult(
                ticket_id=ticket_id,
                requirements=mock_requirements,
                summary=f"Fallback analysis: {str(e)}",
                confidence_score=0.5,
                fallback_used=True
            )
    
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
