"""
Code Generator Agent - LANGUAGE AGNOSTIC VERSION

This agent INFERS language and framework from the repository context.
NEVER assumes a default language. NEVER introduces new languages unless required.
"""

import json
import hashlib
from typing import Dict, Any
from pydantic import ValidationError

from app.schemas.strict_schemas import (
    RequirementSpec, 
    CodeOutput, 
    AgentError,
    GLOBAL_AGENT_RULES
)
from app.utils.logger import logger


# ===========================================
# SYSTEM PROMPT - MULTI-LANGUAGE AWARE
# ===========================================

SYSTEM_PROMPT = f"""{GLOBAL_AGENT_RULES}

You are a Code Generator Agent operating on real repositories.

The repository may contain MULTIPLE programming languages and styles.
You must INFER which languages are present and generate code accordingly.

Your responsibilities:
1. Analyze the repository to detect languages and frameworks present
2. Infer which files and languages are relevant to the requirements
3. Follow existing project conventions PER FILE
4. Generate code ONLY in languages already present in the repository
5. NEVER introduce a new language unless explicitly required and justified

You MUST:
- Detect languages from file extensions (.py, .js, .go, .cls, .cpp, etc.)
- Respect existing file structure and naming conventions
- Match coding patterns per language (error handling, formatting, etc.)
- Generate complete, production-ready code
- Output changes in UNIFIED DIFF FORMAT for reviewability

If multiple languages are involved:
- Modify only the files relevant to the requirements
- Do not refactor unrelated code
- Keep changes minimal and focused

If insufficient context exists:
- List assumptions explicitly in the output

OUTPUT FORMAT - EXACTLY THIS STRUCTURE:
{{
  "changes": [
    {{
      "filepath": "src/services/feature.py",
      "action": "create",
      "language": "python",
      "content": "# Complete file content here\\nimport logging\\n\\nclass Feature:\\n    pass",
      "unified_diff": "diff --git a/src/services/feature.py b/src/services/feature.py\\nnew file mode 100644\\n--- /dev/null\\n+++ b/src/services/feature.py\\n@@ -0,0 +1,5 @@\\n+# Complete file content here\\n+import logging\\n+\\n+class Feature:\\n+    pass",
      "hunks": [
        {{
          "old_start": 0,
          "old_count": 0,
          "new_start": 1,
          "new_count": 5,
          "content": "+# Complete file content here\\n+import logging\\n+\\n+class Feature:\\n+    pass",
          "context": "class Feature"
        }}
      ],
      "purpose": "Implements the core feature logic",
      "implements_requirements": ["REQ-001", "REQ-002"],
      "follows_patterns_from": ["src/services/existing_service.py"],
      "additions": 5,
      "deletions": 0
    }}
  ],
  "languages_detected": ["python", "javascript", "apex"],
  "frameworks_detected": ["fastapi", "react", "salesforce"],
  "integration_steps": [
    "Import Feature in src/services/__init__.py",
    "Add route in src/api/routes.py"
  ],
  "dependencies_required": [],
  "patterns_followed": [
    "Followed logging pattern from existing services",
    "Matched error handling style"
  ],
  "assumptions": []
}}

UNIFIED DIFF FORMAT RULES:
- For NEW files (action: "create"):
  - unified_diff starts with "diff --git a/filepath b/filepath"
  - Include "new file mode 100644"
  - Use "--- /dev/null" and "+++ b/filepath"
  - All lines prefixed with "+"
  
- For MODIFIED files (action: "modify"):
  - unified_diff shows only changed sections
  - Include context lines (3 lines before/after changes)
  - Lines removed prefixed with "-"
  - Lines added prefixed with "+"
  - Unchanged context lines have no prefix (space)
  
- For DELETED files (action: "delete"):
  - unified_diff shows "deleted file mode 100644"
  - All lines prefixed with "-"

CRITICAL RULES:
- "language" field must be INFERRED from file extension and context
- "action" must be one of: "create", "modify", "delete"
- "content" must be COMPLETE code for new files, or the modified sections for changes
- "unified_diff" MUST be provided for all changes
- "hunks" array must contain parsed diff hunks
- "additions" and "deletions" must be accurate counts
- Generate code in the SAME languages as existing files

Output ONLY JSON. No markdown. No explanations."""


class CodeAgentStrict:
    """
    Language-Agnostic Code Generator.
    
    Guarantees:
    - INFERS language from repository context
    - NEVER assumes a default language
    - Returns CodeOutput or raises AgentError
    """
    
    def __init__(self):
        self.name = "CodeGenerator"
        self.retry_count = 1
        logger.info(f"Initialized {self.name} (LANGUAGE-AGNOSTIC MODE)")
    
    async def generate(
        self,
        ticket_id: str,
        requirements: RequirementSpec,
        codebase_context: str,
        codebase_structure: str
    ) -> CodeOutput:
        """
        Generate code based on requirements and repository context.
        Language is INFERRED, not assumed.
        """
        user_prompt = self._build_user_prompt(
            ticket_id, requirements, codebase_context, codebase_structure
        )
        
        input_hash = hashlib.md5(user_prompt.encode()).hexdigest()[:8]
        
        logger.info("=" * 60)
        logger.info(f"[{self.name}] INPUT HASH: {input_hash}")
        logger.info(f"[{self.name}] REQUIREMENTS COUNT: {len(requirements.get_all_requirements())}")
        logger.info(f"[{self.name}] USER PROMPT:\n{user_prompt[:1500]}...")
        logger.info("=" * 60)
        
        for attempt in range(self.retry_count + 1):
            try:
                result = await self._call_llm(user_prompt)
                output = CodeOutput.model_validate(result)
                
                logger.info(f"[{self.name}] SUCCESS: Generated {len(output.changes)} file changes")
                logger.info(f"[{self.name}] DETECTED LANGUAGES: {output.languages_detected}")
                return output
                
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
        requirements: RequirementSpec,
        codebase_context: str,
        codebase_structure: str
    ) -> str:
        """Build user prompt with requirements + context"""
        
        # Format requirements (implementation-neutral)
        req_lines = []
        for req in requirements.get_all_requirements():
            req_lines.append(f"- [{req.id}] ({req.priority.value}) {req.description}")
            if req.acceptance_criteria:
                for ac in req.acceptance_criteria:
                    req_lines.append(f"    AC: {ac}")
        
        parts = [
            f"TICKET ID: {ticket_id}",
            "REQUIREMENTS (implementation-neutral):",
            "\n".join(req_lines),
            f"CONTEXT SUMMARY: {requirements.context_summary}",
            f"PROJECT STRUCTURE (analyze to detect languages):\n{codebase_structure}",
            f"EXISTING CODE (follow patterns and conventions):\n{codebase_context}",
            "TASK: Generate production code that implements ALL requirements, using languages and patterns ALREADY PRESENT in the repository."
        ]
        
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
            max_tokens=8192
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
CodeAgent = CodeAgentStrict
