"""
Test Generator Agent - LANGUAGE AGNOSTIC VERSION

This agent INFERS testing framework from existing tests in the repository.
NEVER assumes a default framework. Adapts to whatever testing approach exists.
"""

import json
import hashlib
from typing import Dict, Any
from pydantic import ValidationError

from app.schemas.strict_schemas import (
    RequirementSpec,
    CodeOutput,
    TestOutput,
    AgentError,
    GLOBAL_AGENT_RULES
)
from app.utils.logger import logger


# ===========================================
# SYSTEM PROMPT - FRAMEWORK-INFERRED
# ===========================================

SYSTEM_PROMPT = f"""{GLOBAL_AGENT_RULES}

You are a Test Generator Agent.

Your responsibility is to generate automated tests that validate
the provided code changes and requirements.

Repositories may contain:
- Multiple test frameworks (pytest, jest, go test, @isTest, gtest, etc.)
- Multiple languages
- No tests at all (in which case, propose minimal idiomatic approach)

You MUST:
1. Analyze the repository for existing test files and patterns
2. INFER the testing framework from existing tests
3. Match testing style, structure, and conventions
4. Generate tests in the SAME language as the code under test
5. Avoid introducing new frameworks unless explicitly required

If existing tests are found:
- Use the same framework and patterns
- Place tests in the same location convention (tests/, __tests__/, *Test.cls, etc.)
- Follow naming conventions

If NO tests exist:
- Propose the minimal, idiomatic testing approach for the detected language
- Clearly state this assumption in the output

OUTPUT FORMAT - EXACTLY THIS STRUCTURE:
{{
  "testing_framework": "pytest",
  "framework_evidence": "Found existing test files using pytest in tests/ directory with conftest.py",
  "tests": [
    {{
      "name": "test_feature_success",
      "description": "Verifies the feature works with valid input",
      "test_type": "unit",
      "target_file": "src/services/feature.py",
      "covers_requirement": "REQ-001",
      "code": "def test_feature_success():\\n    from src.services.feature import Feature\\n    result = Feature().process()\\n    assert result is not None",
      "assertions_count": 1
    }}
  ],
  "test_file_path": "tests/test_feature.py",
  "test_file_content": "# Complete test file content here\\nimport pytest\\n\\ndef test_feature_success():\\n    ...",
  "setup_instructions": ["Run: pytest tests/test_feature.py"],
  "coverage_analysis": "REQ-001 covered by test_feature_success. REQ-002 covered by test_feature_edge_case.",
  "assumptions": []
}}

FRAMEWORK EXAMPLES (detect from context, don't assume):
- Python: pytest, unittest
- JavaScript: jest, vitest, mocha
- Go: testing package
- C++: gtest, catch2
- Java: JUnit
- Apex: @isTest annotation
- Rust: built-in #[test]
- Ruby: rspec, minitest

CRITICAL RULES:
- "testing_framework" must be INFERRED from existing files
- "framework_evidence" must explain HOW you detected the framework
- Tests must use the SAME language as the code being tested
- Each test must have at least one assertion
- test_type must be: "unit", "integration", or "e2e"

Output ONLY JSON. No markdown. No explanations."""


class TestAgentStrict:
    """
    Language-Agnostic Test Generator.
    
    Guarantees:
    - INFERS testing framework from repository
    - NEVER assumes a default framework
    - Returns TestOutput or raises AgentError
    """
    
    def __init__(self):
        self.name = "TestGenerator"
        self.retry_count = 1
        logger.info(f"Initialized {self.name} (LANGUAGE-AGNOSTIC MODE)")
    
    async def generate(
        self,
        ticket_id: str,
        requirements: RequirementSpec,
        generated_code: CodeOutput
    ) -> TestOutput:
        """
        Generate tests for the generated code.
        Framework is INFERRED from existing tests.
        """
        user_prompt = self._build_user_prompt(ticket_id, requirements, generated_code)
        
        input_hash = hashlib.md5(user_prompt.encode()).hexdigest()[:8]
        
        logger.info("=" * 60)
        logger.info(f"[{self.name}] INPUT HASH: {input_hash}")
        logger.info(f"[{self.name}] FILES TO TEST: {[f.filepath for f in generated_code.changes]}")
        logger.info(f"[{self.name}] DETECTED LANGUAGES: {generated_code.languages_detected}")
        logger.info("=" * 60)
        
        for attempt in range(self.retry_count + 1):
            try:
                result = await self._call_llm(user_prompt)
                output = TestOutput.model_validate(result)
                
                logger.info(f"[{self.name}] SUCCESS: Generated {len(output.tests)} tests")
                logger.info(f"[{self.name}] INFERRED FRAMEWORK: {output.testing_framework}")
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
        generated_code: CodeOutput
    ) -> str:
        """Build user prompt with code + requirements"""
        
        # Format requirements
        req_lines = []
        for req in requirements.get_all_requirements():
            req_lines.append(f"- {req.id}: {req.description}")
        
        # Format generated code
        code_sections = []
        for change in generated_code.changes:
            code_sections.append(
                f"FILE: {change.filepath}\n"
                f"LANGUAGE: {change.language}\n"
                f"ACTION: {change.action}\n"
                f"IMPLEMENTS: {', '.join(change.implements_requirements)}\n"
                f"CODE:\n```\n{change.content}\n```"
            )
        
        parts = [
            f"TICKET ID: {ticket_id}",
            "REQUIREMENTS TO COVER:",
            "\n".join(req_lines),
            f"DETECTED LANGUAGES IN REPO: {', '.join(generated_code.languages_detected)}",
            f"DETECTED FRAMEWORKS: {', '.join(generated_code.frameworks_detected) if generated_code.frameworks_detected else 'None detected'}",
            "GENERATED CODE TO TEST:",
            "\n\n".join(code_sections),
            "TASK: Generate tests using the INFERRED testing framework. If no tests exist in the repo, propose the minimal idiomatic approach for the detected language(s)."
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
TestAgent = TestAgentStrict
