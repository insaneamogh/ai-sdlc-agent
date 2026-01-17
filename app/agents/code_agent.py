"""
Code Generator Agent

This agent is responsible for generating code based on:
- Extracted requirements
- Existing code patterns (via RAG)
- Coding standards and best practices
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.logger import logger


class GeneratedFile(BaseModel):
    """Model for a generated code file"""
    filename: str
    language: str
    content: str
    description: str
    line_count: int = 0


class CodeGenerationResult(BaseModel):
    """Result of code generation"""
    ticket_id: str
    files: List[GeneratedFile]
    summary: str
    patterns_used: List[str] = []
    confidence_score: float = Field(ge=0.0, le=1.0)


class CodeAgent:
    """
    Agent for generating code based on requirements.
    
    This agent uses LLM with RAG to:
    1. Understand requirements
    2. Fetch similar code patterns from vector store
    3. Generate code following existing patterns
    4. Apply coding standards
    
    Example usage:
        agent = CodeAgent()
        result = await agent.generate(requirements, context)
    """
    
    def __init__(self, llm=None, vectorstore=None, model: str = None):
        """
        Initialize the Code Agent.
        
        Args:
            llm: Optional LLM instance
            vectorstore: Optional vector store for RAG
            model: Optional model name to use. If not provided, uses config default.
        """
        self.llm = llm
        self.vectorstore = vectorstore
        self.model = model  # Store model override
        self.name = "CodeGenerator"
        logger.info(f"Initialized {self.name} with model={model or 'default'}")
    
    async def generate(
        self,
        ticket_id: str,
        requirements: List[Dict[str, Any]],
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> CodeGenerationResult:
        """
        Generate code based on requirements.
        
        Args:
            ticket_id: The Jira ticket ID
            requirements: List of extracted requirements
            language: Target programming language
            context: Optional additional context (e.g., existing code patterns)
        
        Returns:
            CodeGenerationResult with generated files
        """
        logger.info(f"Generating code for ticket: {ticket_id}")
        
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
            
            # Format requirements for the prompt
            req_text = "\n".join([
                f"- {r.get('description', r.get('id', 'Requirement'))}" 
                for r in requirements
            ]) if requirements else "No specific requirements provided"
            
            system_prompt = """You are an expert software engineer. Generate production-quality code based on the given requirements.

Return ONLY valid JSON in this exact format (no markdown code blocks around the JSON):
{
  "files": [
    {
      "filename": "module_name.py",
      "language": "python",
      "content": "# Full code content here...",
      "description": "What this file does"
    }
  ],
  "summary": "Brief summary of generated code",
  "patterns_used": ["pattern1", "pattern2"],
  "confidence_score": 0.85
}

Generate clean, well-documented, production-ready code with proper error handling."""

            user_prompt = f"""Generate code for these requirements:

REQUIREMENTS:
{req_text}

CONTEXT:
{json.dumps(context) if context else 'No additional context'}

Generate 2-3 Python files that implement these requirements with:
1. Main implementation file
2. Utility/helper functions
3. Proper docstrings and type hints"""

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
            
            files = []
            for f in parsed.get("files", []):
                content = f.get("content", "")
                files.append(GeneratedFile(
                    filename=f.get("filename", "generated.py"),
                    language=f.get("language", "python"),
                    content=content,
                    description=f.get("description", "Generated file"),
                    line_count=len(content.split("\n"))
                ))
            
            result = CodeGenerationResult(
                ticket_id=ticket_id,
                files=files,
                summary=parsed.get("summary", f"Generated {len(files)} files"),
                patterns_used=parsed.get("patterns_used", []),
                confidence_score=parsed.get("confidence_score", 0.8)
            )
            
            logger.info(f"Completed code generation for {ticket_id}: {len(files)} files generated")
            return result
            
        except Exception as e:
            logger.error(f"LLM code generation failed: {e}, falling back to mock data")
            # Fallback to mock data on error
            mock_files = [
                GeneratedFile(
                    filename="implementation.py",
                    language="python",
                    content=self._generate_mock_code(requirements),
                    description=f"Generated code (fallback due to: {str(e)[:50]})",
                    line_count=25
                )
            ]
            
            return CodeGenerationResult(
                ticket_id=ticket_id,
                files=mock_files,
                summary=f"Fallback generation: {str(e)}",
                patterns_used=[],
                confidence_score=0.5
            )
    
    def _generate_mock_code(self, requirements: List[Dict[str, Any]]) -> str:
        """Generate mock code for demonstration"""
        return '''"""
Authentication Module

Generated based on extracted requirements.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    """User model for authentication"""
    id: str
    email: str
    is_authenticated: bool = False


class AuthenticationService:
    """Service for handling user authentication"""
    
    def __init__(self):
        self._users = {}
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        # TODO: Implement actual authentication logic
        # This is a placeholder implementation
        
        if not email or not password:
            return None
        
        # Validate credentials against identity provider
        user = User(
            id="user_123",
            email=email,
            is_authenticated=True
        )
        
        return user
    
    async def logout(self, user_id: str) -> bool:
        """
        Logout a user.
        
        Args:
            user_id: The user's ID
        
        Returns:
            True if logout successful
        """
        # TODO: Implement logout logic
        return True
'''
    
    def _generate_mock_utils(self) -> str:
        """Generate mock utility code"""
        return '''"""
Authentication Utilities

Helper functions for authentication module.
"""

import hashlib
import secrets
from typing import Optional


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def validate_email(email: str) -> bool:
    """Basic email validation"""
    return "@" in email and "." in email
'''
    
    async def fetch_similar_patterns(
        self,
        requirements: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch similar code patterns from vector store.
        
        Args:
            requirements: Requirements to match against
            limit: Maximum number of patterns to return
        
        Returns:
            List of similar code patterns
        """
        if not self.vectorstore:
            logger.warning("No vector store configured, skipping pattern retrieval")
            return []
        
        # TODO: Implement actual RAG retrieval
        # 1. Convert requirements to embedding query
        # 2. Search vector store for similar code
        # 3. Return relevant patterns
        
        return []
    
    def _create_generation_prompt(
        self,
        requirements: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        language: str
    ) -> str:
        """
        Create the prompt for code generation.
        
        This will be used with LangChain's prompt templates.
        """
        prompt = f"""Generate {language} code based on the following requirements.

REQUIREMENTS:
"""
        for i, req in enumerate(requirements, 1):
            prompt += f"{i}. {req.get('description', 'No description')}\n"
        
        if patterns:
            prompt += "\nEXISTING PATTERNS TO FOLLOW:\n"
            for pattern in patterns:
                prompt += f"- {pattern.get('name', 'Unknown pattern')}\n"
        
        prompt += """
Please generate clean, well-documented code that:
1. Implements all requirements
2. Follows the existing patterns
3. Includes proper error handling
4. Has clear docstrings and comments
5. Is production-ready

Return the code with clear file separations."""
        
        return prompt
