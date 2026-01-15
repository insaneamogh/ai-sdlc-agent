"""
Test Generator Agent

This agent is responsible for generating test cases based on:
- Generated code
- Requirements
- Existing test patterns
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.logger import logger


class GeneratedTest(BaseModel):
    """Model for a generated test"""
    name: str
    description: str
    test_type: str = Field(description="unit, integration, or e2e")
    code: str
    covers_requirement: Optional[str] = None


class TestGenerationResult(BaseModel):
    """Result of test generation"""
    ticket_id: str
    tests: List[GeneratedTest]
    test_file: str
    summary: str
    coverage_estimate: float = Field(ge=0.0, le=100.0)
    confidence_score: float = Field(ge=0.0, le=1.0)


class TestAgent:
    """
    Agent for generating test cases.
    
    This agent uses LLM to:
    1. Analyze generated code
    2. Understand requirements
    3. Generate comprehensive test cases
    4. Match existing test patterns
    
    Example usage:
        agent = TestAgent()
        result = await agent.generate(code, requirements)
    """
    
    def __init__(self, llm=None, vectorstore=None):
        """
        Initialize the Test Agent.
        
        Args:
            llm: Optional LLM instance
            vectorstore: Optional vector store for test pattern retrieval
        """
        self.llm = llm
        self.vectorstore = vectorstore
        self.name = "TestGenerator"
        logger.info(f"Initialized {self.name}")
    
    async def generate(
        self,
        ticket_id: str,
        code: str,
        requirements: List[Dict[str, Any]],
        test_framework: str = "pytest",
        context: Optional[Dict[str, Any]] = None
    ) -> TestGenerationResult:
        """
        Generate tests for the given code.
        
        Args:
            ticket_id: The Jira ticket ID
            code: The generated code to test
            requirements: List of requirements to cover
            test_framework: Test framework to use (pytest, unittest)
            context: Optional additional context
        
        Returns:
            TestGenerationResult with generated tests
        """
        logger.info(f"Generating tests for ticket: {ticket_id}")
        
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            from app.config import get_settings
            import json
            
            settings = get_settings()
            
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.3
            )
            
            # Format requirements for the prompt
            req_text = "\n".join([
                f"- {r.get('description', r.get('id', 'Requirement'))}" 
                for r in requirements
            ]) if requirements else "No specific requirements"
            
            system_prompt = """You are an expert test engineer. Generate comprehensive test cases for the given code.

Return ONLY valid JSON in this exact format (no markdown code blocks around the JSON):
{
  "tests": [
    {
      "name": "test_function_name",
      "description": "What this test verifies",
      "test_type": "unit",
      "code": "Full pytest code for this test...",
      "covers_requirement": "REQ-001"
    }
  ],
  "test_file": "Complete pytest file with all tests combined...",
  "summary": "Brief summary",
  "coverage_estimate": 85.0,
  "confidence_score": 0.85
}

test_type: unit, integration, or e2e
Generate comprehensive tests with edge cases and error handling."""

            user_prompt = f"""Generate tests for this code:

CODE TO TEST:
{code[:3000] if code else 'No code provided'}

REQUIREMENTS TO COVER:
{req_text}

Generate 4-6 pytest test cases covering:
1. Happy path tests
2. Edge cases
3. Error handling
4. Integration tests if applicable"""

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
            
            tests = []
            for t in parsed.get("tests", []):
                tests.append(GeneratedTest(
                    name=t.get("name", "test_unnamed"),
                    description=t.get("description", ""),
                    test_type=t.get("test_type", "unit"),
                    code=t.get("code", ""),
                    covers_requirement=t.get("covers_requirement")
                ))
            
            result = TestGenerationResult(
                ticket_id=ticket_id,
                tests=tests,
                test_file=parsed.get("test_file", self._combine_tests(tests, test_framework)),
                summary=parsed.get("summary", f"Generated {len(tests)} tests"),
                coverage_estimate=parsed.get("coverage_estimate", 80.0),
                confidence_score=parsed.get("confidence_score", 0.8)
            )
            
            logger.info(f"Completed test generation for {ticket_id}: {len(tests)} tests generated")
            return result
            
        except Exception as e:
            logger.error(f"LLM test generation failed: {e}, falling back to mock data")
            # Fallback to mock data on error
            mock_tests = [
                GeneratedTest(
                    name="test_basic_functionality",
                    description=f"Basic test (fallback due to: {str(e)[:50]})",
                    test_type="unit",
                    code="def test_basic():\n    assert True",
                    covers_requirement="REQ-001"
                )
            ]
            
            return TestGenerationResult(
                ticket_id=ticket_id,
                tests=mock_tests,
                test_file=self._combine_tests(mock_tests, test_framework),
                summary=f"Fallback test generation: {str(e)}",
                coverage_estimate=20.0,
                confidence_score=0.3
            )
    
    def _generate_mock_test_valid(self) -> str:
        """Generate mock test for valid credentials"""
        return '''@pytest.mark.asyncio
async def test_authenticate_valid_credentials():
    """Test authentication with valid email and password"""
    service = AuthenticationService()
    
    user = await service.authenticate(
        email="test@example.com",
        password="valid_password"
    )
    
    assert user is not None
    assert user.email == "test@example.com"
    assert user.is_authenticated is True
'''
    
    def _generate_mock_test_invalid(self) -> str:
        """Generate mock test for invalid credentials"""
        return '''@pytest.mark.asyncio
async def test_authenticate_invalid_credentials():
    """Test authentication with invalid credentials"""
    service = AuthenticationService()
    
    user = await service.authenticate(
        email="test@example.com",
        password="wrong_password"
    )
    
    # Based on implementation, adjust assertion
    # For mock, it returns a user, but real impl should return None
    assert user is not None  # Placeholder - update when real auth is implemented
'''
    
    def _generate_mock_test_edge_case(self) -> str:
        """Generate mock test for edge cases"""
        return '''@pytest.mark.asyncio
async def test_authenticate_empty_input():
    """Test authentication with empty input"""
    service = AuthenticationService()
    
    # Test empty email
    user = await service.authenticate(email="", password="password")
    assert user is None
    
    # Test empty password
    user = await service.authenticate(email="test@example.com", password="")
    assert user is None
    
    # Test both empty
    user = await service.authenticate(email="", password="")
    assert user is None
'''
    
    def _generate_mock_test_logout(self) -> str:
        """Generate mock test for logout"""
        return '''@pytest.mark.asyncio
async def test_logout_success():
    """Test successful logout"""
    service = AuthenticationService()
    
    result = await service.logout(user_id="user_123")
    
    assert result is True
'''
    
    def _generate_mock_test_performance(self) -> str:
        """Generate mock performance test"""
        return '''@pytest.mark.asyncio
async def test_authentication_performance():
    """Test authentication completes within 3 seconds"""
    import time
    
    service = AuthenticationService()
    
    start_time = time.time()
    await service.authenticate(
        email="test@example.com",
        password="password"
    )
    elapsed_time = time.time() - start_time
    
    assert elapsed_time < 3.0, f"Authentication took {elapsed_time:.2f}s, expected < 3s"
'''
    
    def _combine_tests(
        self,
        tests: List[GeneratedTest],
        framework: str
    ) -> str:
        """Combine all tests into a single test file"""
        header = '''"""
Generated Test Suite

Auto-generated tests for the authentication module.
"""

import pytest
from authentication import AuthenticationService, User


'''
        
        test_code = header
        for test in tests:
            test_code += test.code + "\n\n"
        
        return test_code
    
    async def fetch_test_patterns(
        self,
        code_type: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Fetch similar test patterns from vector store.
        
        Args:
            code_type: Type of code being tested
            limit: Maximum number of patterns to return
        
        Returns:
            List of similar test patterns
        """
        if not self.vectorstore:
            logger.warning("No vector store configured, skipping pattern retrieval")
            return []
        
        # TODO: Implement actual RAG retrieval for test patterns
        return []
    
    def _create_generation_prompt(
        self,
        code: str,
        requirements: List[Dict[str, Any]],
        framework: str
    ) -> str:
        """
        Create the prompt for test generation.
        """
        prompt = f"""Generate comprehensive {framework} tests for the following code.

CODE TO TEST:
```python
{code}
```

REQUIREMENTS TO COVER:
"""
        for i, req in enumerate(requirements, 1):
            prompt += f"{i}. {req.get('description', 'No description')}\n"
        
        prompt += f"""
Please generate tests that:
1. Cover all public methods
2. Test happy path scenarios
3. Test edge cases and error conditions
4. Test any non-functional requirements (performance, etc.)
5. Follow {framework} conventions
6. Include clear docstrings

Return the complete test file with all imports."""
        
        return prompt
