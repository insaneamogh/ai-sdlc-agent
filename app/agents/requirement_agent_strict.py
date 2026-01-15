"""
Requirement Analyzer Agent - LANGUAGE AGNOSTIC VERSION

This agent extracts IMPLEMENTATION-NEUTRAL requirements.
NO language mentions. NO framework bias. NO implementation decisions.
"""

import json
import hashlib
from typing import Optional, Dict, Any
from pydantic import ValidationError

from app.schemas.strict_schemas import RequirementSpec, AgentError, GLOBAL_AGENT_RULES
from app.utils.logger import logger


# ===========================================
# SYSTEM PROMPT - IMPLEMENTATION NEUTRAL
# ===========================================

SYSTEM_PROMPT = f"""{GLOBAL_AGENT_RULES}

You are a Requirement Analyzer Agent.

Your responsibility is to extract structured software requirements
from SDLC artifacts such as tickets, descriptions, and repository context.

You do NOT:
- Generate code
- Reference specific programming languages
- Reference specific frameworks
- Make implementation decisions
- Suggest technical solutions

You MUST:
- Produce implementation-agnostic requirements
- Describe BEHAVIOR, not implementation
- Separate functional vs non-functional concerns
- Identify edge cases
- Identify ambiguities and list assumptions
- Analyze the repository to understand the problem domain (not the tech stack)

OUTPUT FORMAT - EXACTLY THIS STRUCTURE (ALL FIELDS REQUIRED):
{{
  "functional_requirements": [
    {{
      "id": "REQ-001",
      "type": "functional",
      "description": "The system shall allow users to retrieve dashboard data",
      "priority": "high",
      "acceptance_criteria": ["Dashboard loads within 3 seconds"],
      "edge_cases": ["Empty data state"],
      "ambiguities": []
    }}
  ],
  "non_functional_requirements": [],
  "constraints": [],
  "assumptions": ["Assumes authenticated users only"],
  "context_summary": "REQUIRED: A brief summary of what this system/feature does"
}}

REQUIRED FIELDS (must be present):
- functional_requirements: list (at least 1 item)
- non_functional_requirements: list (can be empty [])
- constraints: list (can be empty [])
- assumptions: list (can be empty [])
- context_summary: string (REQUIRED - brief summary of the domain)

ID PREFIXES (use appropriate prefix):
- Functional requirements: "REQ-001", "REQ-002", etc.
- Non-functional requirements: "NFR-001", "NFR-002", etc.
- Constraints: "CON-001", "CON-002", etc.

ENUM VALUES (use EXACTLY as shown):
- type: "functional" | "non-functional" | "constraint" (MUST use hyphen!)
- priority: "high" | "medium" | "low"

CRITICAL: Do NOT mention programming languages, frameworks, or technical implementations.
Focus on WHAT the system does, not HOW it does it.

Output ONLY valid JSON. No markdown. No code blocks. No explanations."""


class RequirementAgentStrict:
    """
    Language-Agnostic Requirement Analyzer.
    
    Guarantees:
    - Returns RequirementSpec or raises AgentError
    - NEVER mentions specific languages or frameworks
    - Focus on behavior, not implementation
    """
    
    def __init__(self):
        self.name = "RequirementAnalyzer"
        self.retry_count = 1
        logger.info(f"Initialized {self.name} (LANGUAGE-AGNOSTIC MODE)")
    
    async def analyze(
        self,
        ticket_id: str,
        title: str,
        description: str,
        codebase_context: str,
        acceptance_criteria: Optional[str] = None
    ) -> RequirementSpec:
        """
        Analyze ticket + codebase and extract IMPLEMENTATION-NEUTRAL requirements.
        """
        user_prompt = self._build_user_prompt(
            ticket_id, title, description, codebase_context, acceptance_criteria
        )
        
        input_hash = hashlib.md5(user_prompt.encode()).hexdigest()[:8]
        
        # LOG EXACT PROMPTS
        logger.info("=" * 60)
        logger.info(f"[{self.name}] INPUT HASH: {input_hash}")
        logger.info(f"[{self.name}] SYSTEM PROMPT LENGTH: {len(SYSTEM_PROMPT)}")
        logger.info(f"[{self.name}] USER PROMPT:\n{user_prompt[:1000]}...")
        logger.info("=" * 60)
        
        for attempt in range(self.retry_count + 1):
            try:
                result = await self._call_llm(user_prompt)
                spec = RequirementSpec.model_validate(result)
                
                logger.info(f"[{self.name}] SUCCESS: Extracted {len(spec.get_all_requirements())} requirements")
                return spec
                
            except ValidationError as e:
                logger.error(f"[{self.name}] VALIDATION FAILED (attempt {attempt + 1}): {e}")
                if attempt == self.retry_count:
                    raise Exception(
                        AgentError(
                            agent_name=self.name,
                            error_type="validation_error",
                            message=f"Output did not match schema: {str(e)}",
                            retry_possible=False,
                            input_hash=input_hash
                        ).model_dump_json()
                    )
            except json.JSONDecodeError as e:
                logger.error(f"[{self.name}] JSON PARSE FAILED (attempt {attempt + 1}): {e}")
                if attempt == self.retry_count:
                    raise Exception(
                        AgentError(
                            agent_name=self.name,
                            error_type="json_parse_error",
                            message=f"LLM did not return valid JSON: {str(e)}",
                            retry_possible=True,
                            input_hash=input_hash
                        ).model_dump_json()
                    )
            except Exception as e:
                logger.error(f"[{self.name}] UNEXPECTED ERROR: {e}")
                raise Exception(
                    AgentError(
                        agent_name=self.name,
                        error_type="unknown_error",
                        message=str(e),
                        retry_possible=False,
                        input_hash=input_hash
                    ).model_dump_json()
                )
    
    def _build_user_prompt(
        self,
        ticket_id: str,
        title: str,
        description: str,
        codebase_context: str,
        acceptance_criteria: Optional[str]
    ) -> str:
        """Build user prompt with PURE DATA - no instructions"""
        parts = [
            f"TICKET ID: {ticket_id}",
            f"TITLE: {title}",
            f"DESCRIPTION:\n{description}",
        ]
        
        if acceptance_criteria:
            parts.append(f"ACCEPTANCE CRITERIA:\n{acceptance_criteria}")
        
        parts.append(f"REPOSITORY CONTEXT (for understanding the domain, NOT for implementation details):\n{codebase_context}")
        
        return "\n\n".join(parts)
    
    async def _call_llm(self, user_prompt: str) -> Dict[str, Any]:
        """Call LLM with deterministic settings"""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from app.config import get_settings
        
        settings = get_settings()
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            top_p=1,
            max_tokens=4096
        )
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        response = await llm.ainvoke(messages)
        response_text = self._clean_json_response(response.content.strip())
        
        return json.loads(response_text)
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks if present"""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return text.strip()


# Backwards compatibility
RequirementAgent = RequirementAgentStrict
