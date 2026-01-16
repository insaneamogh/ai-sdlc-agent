"""
Code Generator Agent Strategies

Standard and Strict strategy implementations for code generation.
Produces Git-style diffs instead of raw code dumps.
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


class DiffHunk(BaseModel):
    """A single diff hunk"""
    file: str
    old_start: int = 1
    old_count: int = 0
    new_start: int = 1
    new_count: int = 0
    content: str
    description: str = ""


class GeneratedFile(BaseModel):
    """Model for a generated code file"""
    filename: str
    language: str
    content: str
    description: str
    line_count: int = 0
    is_new: bool = True


class ImpactAnalysis(BaseModel):
    """Analysis of code change impact"""
    affected_classes: List[str] = Field(default_factory=list)
    affected_methods: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    breaking_change_risk: str = Field(default="low", description="low, medium, high")
    migration_notes: List[str] = Field(default_factory=list)


class CodeOutput(AgentOutput):
    """Output from code generation - produces diffs, not raw code"""
    ticket_id: str
    files_modified: List[str] = Field(default_factory=list)
    diff_hunks: List[DiffHunk] = Field(default_factory=list)
    generated_files: List[GeneratedFile] = Field(default_factory=list)
    unified_diff: str = ""
    patterns_used: List[str] = Field(default_factory=list)
    impact_analysis: ImpactAnalysis = Field(default_factory=ImpactAnalysis)
    summary: str = ""
    
    def get_full_diff(self) -> str:
        """Get the complete unified diff"""
        if self.unified_diff:
            return self.unified_diff
        
        # Generate from hunks
        diff_parts = []
        for hunk in self.diff_hunks:
            diff_parts.append(f"diff --git a/{hunk.file} b/{hunk.file}")
            diff_parts.append(f"--- a/{hunk.file}")
            diff_parts.append(f"+++ b/{hunk.file}")
            diff_parts.append(f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@")
            diff_parts.append(hunk.content)
        
        return "\n".join(diff_parts)


class StandardCodeStrategy(AgentStrategy[CodeOutput]):
    """
    Standard strategy for code generation.
    
    Produces unified diffs with reasoning traces.
    """
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.STANDARD
    
    def get_system_prompt(self) -> str:
        return """You are an expert software engineer. Generate production-quality code based on the given requirements.

CRITICAL: Output code as UNIFIED DIFF format, not raw code dumps.

Return ONLY valid JSON in this exact format:
{
  "files_modified": ["module.py"],
  "diff_hunks": [
    {
      "file": "module.py",
      "old_start": 1,
      "old_count": 0,
      "new_start": 1,
      "new_count": 15,
      "content": "+def new_function():\\n+    '''Docstring'''\\n+    pass",
      "description": "Added new function"
    }
  ],
  "generated_files": [
    {
      "filename": "module.py",
      "language": "python",
      "content": "Full file content...",
      "description": "Main implementation",
      "line_count": 50,
      "is_new": true
    }
  ],
  "patterns_used": ["singleton", "factory"],
  "impact_analysis": {
    "affected_classes": ["ClassName"],
    "affected_methods": ["method_name"],
    "affected_tests": ["test_file.py"],
    "breaking_change_risk": "low",
    "migration_notes": []
  },
  "summary": "Brief summary of changes",
  "confidence_score": 0.85,
  "reasoning_trace": [
    "Analyzed requirements",
    "Matched existing pattern from codebase",
    "Applied error handling conventions"
  ],
  "rag_sources_used": ["similar_file.py", "PR-123"]
}

Generate clean, well-documented, production-ready code with:
- Proper error handling
- Type hints
- Docstrings
- Following existing patterns"""
    
    def get_user_prompt(self, **kwargs) -> str:
        requirements = kwargs.get("requirements", [])
        context = kwargs.get("context", {})
        language = kwargs.get("language", "python")
        
        req_text = "\n".join([
            f"- {r.get('description', r.get('id', 'Requirement'))}" 
            for r in requirements
        ]) if requirements else "No specific requirements provided"
        
        prompt = f"""Generate {language} code for these requirements:

REQUIREMENTS:
{req_text}

CONTEXT:
{json.dumps(context) if context else 'No additional context'}

Generate code as unified diff format showing:
1. What files are created/modified
2. The actual code changes
3. Impact analysis of the changes

Include proper error handling, type hints, and documentation."""
        
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response"""
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
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "files_modified": [],
                "diff_hunks": [],
                "generated_files": [],
                "patterns_used": [],
                "impact_analysis": {},
                "summary": "Failed to parse response",
                "confidence_score": 0.0,
                "reasoning_trace": [],
                "rag_sources_used": []
            }
    
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> CodeOutput:
        """Create CodeOutput from parsed data"""
        ticket_id = kwargs.get("ticket_id", "UNKNOWN")
        
        # Parse diff hunks
        hunks = []
        for h in parsed_data.get("diff_hunks", []):
            hunks.append(DiffHunk(
                file=h.get("file", "unknown.py"),
                old_start=h.get("old_start", 1),
                old_count=h.get("old_count", 0),
                new_start=h.get("new_start", 1),
                new_count=h.get("new_count", 0),
                content=h.get("content", ""),
                description=h.get("description", "")
            ))
        
        # Parse generated files
        files = []
        for f in parsed_data.get("generated_files", []):
            content = f.get("content", "")
            files.append(GeneratedFile(
                filename=f.get("filename", "generated.py"),
                language=f.get("language", "python"),
                content=content,
                description=f.get("description", ""),
                line_count=f.get("line_count", len(content.split("\n"))),
                is_new=f.get("is_new", True)
            ))
        
        # Parse impact analysis
        impact_data = parsed_data.get("impact_analysis", {})
        impact = ImpactAnalysis(
            affected_classes=impact_data.get("affected_classes", []),
            affected_methods=impact_data.get("affected_methods", []),
            affected_tests=impact_data.get("affected_tests", []),
            breaking_change_risk=impact_data.get("breaking_change_risk", "low"),
            migration_notes=impact_data.get("migration_notes", [])
        )
        
        total_files = len(files) + len(hunks)
        confidence = parsed_data.get("confidence_score", 0.8 if total_files > 0 else 0.0)
        
        return CodeOutput(
            agent_name="CodeGenerator",
            mode=self.mode,
            ticket_id=ticket_id,
            files_modified=parsed_data.get("files_modified", [f.filename for f in files]),
            diff_hunks=hunks,
            generated_files=files,
            patterns_used=parsed_data.get("patterns_used", []),
            impact_analysis=impact,
            summary=parsed_data.get("summary", f"Generated {len(files)} files"),
            quality_metrics=QualityMetrics(
                confidence_score=confidence,
                completeness_score=min(1.0, total_files / 3),
                items_count=total_files,
                has_errors=total_files == 0
            ),
            reasoning_trace=ReasoningTrace(
                steps=parsed_data.get("reasoning_trace", []),
                rag_sources_used=parsed_data.get("rag_sources_used", []),
                patterns_matched=parsed_data.get("patterns_used", [])
            )
        )


class StrictCodeStrategy(AgentStrategy[CodeOutput]):
    """
    Strict strategy for code generation.
    
    Enforces comprehensive diff output with full impact analysis.
    """
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.STRICT
    
    def get_system_prompt(self) -> str:
        return """You are a senior software architect with 20 years of experience. Generate PRODUCTION-READY code that can be directly merged into a codebase.

CRITICAL REQUIREMENTS:
1. Output MUST be in unified diff format
2. Every function MUST have docstrings and type hints
3. Error handling MUST be comprehensive
4. Impact analysis MUST be complete
5. Code MUST follow SOLID principles

Return ONLY valid JSON in this EXACT format:
{
  "files_modified": ["module.py", "utils.py"],
  "diff_hunks": [
    {
      "file": "module.py",
      "old_start": 1,
      "old_count": 0,
      "new_start": 1,
      "new_count": 25,
      "content": "+from typing import Optional, List\\n+\\n+def calculate_tax(income: float) -> float:\\n+    '''\\n+    Calculate tax based on income slab.\\n+    \\n+    Args:\\n+        income: Annual income in currency units\\n+    \\n+    Returns:\\n+        Calculated tax amount\\n+    \\n+    Raises:\\n+        ValueError: If income is negative or None\\n+    '''\\n+    if income is None or income < 0:\\n+        raise ValueError('Invalid income value')\\n+    \\n+    if income <= 250000:\\n+        return 0.0\\n+    elif income <= 500000:\\n+        return (income - 250000) * 0.05\\n+    else:\\n+        return 12500 + (income - 500000) * 0.20",
      "description": "Added tax calculation function with full validation"
    }
  ],
  "generated_files": [
    {
      "filename": "module.py",
      "language": "python",
      "content": "Complete file content with all imports, classes, functions...",
      "description": "Main implementation module",
      "line_count": 50,
      "is_new": true
    }
  ],
  "patterns_used": ["input-validation", "error-handling", "type-hints"],
  "impact_analysis": {
    "affected_classes": ["TaxCalculator"],
    "affected_methods": ["calculate_tax", "validate_income"],
    "affected_tests": ["test_tax.py::test_calculate_tax"],
    "breaking_change_risk": "low",
    "migration_notes": ["No breaking changes", "New function added"]
  },
  "summary": "Implemented tax calculation with comprehensive validation",
  "confidence_score": 0.92,
  "reasoning_trace": [
    "Step 1: Analyzed requirement for tax calculation",
    "Step 2: Identified input validation needs",
    "Step 3: Applied existing error handling pattern",
    "Step 4: Added comprehensive type hints",
    "Step 5: Documented with Google-style docstrings"
  ],
  "rag_sources_used": ["existing_calculator.py", "PR-456"]
}

MINIMUM REQUIREMENTS:
- At least 1 generated file
- Complete diff hunks for all changes
- Full impact analysis
- At least 3 reasoning steps"""
    
    def get_user_prompt(self, **kwargs) -> str:
        requirements = kwargs.get("requirements", [])
        context = kwargs.get("context", {})
        language = kwargs.get("language", "python")
        
        req_text = "\n".join([
            f"- [{r.get('id', 'REQ')}] {r.get('description', 'Requirement')}" 
            for r in requirements
        ]) if requirements else "No specific requirements provided"
        
        prompt = f"""STRICT CODE GENERATION REQUIRED

Generate production-ready {language} code for:

REQUIREMENTS:
{req_text}

CONTEXT:
{json.dumps(context, indent=2) if context else 'No additional context'}

MANDATORY OUTPUT:
1. Unified diff format for all changes
2. Complete file content for new files
3. Full impact analysis
4. Reasoning trace explaining decisions
5. RAG sources if patterns were matched

Code MUST include:
- Type hints on all functions
- Docstrings with Args/Returns/Raises
- Comprehensive error handling
- Input validation
- Following existing codebase patterns"""
        
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
            files_count = len(data.get("generated_files", []))
            hunks_count = len(data.get("diff_hunks", []))
            reasoning_count = len(data.get("reasoning_trace", []))
            
            warnings = []
            if files_count == 0 and hunks_count == 0:
                warnings.append("No code generated")
            if reasoning_count < 3:
                warnings.append(f"Only {reasoning_count} reasoning steps (minimum 3)")
            
            data["validation_warnings"] = warnings
            return data
            
        except json.JSONDecodeError:
            return {
                "files_modified": [],
                "diff_hunks": [],
                "generated_files": [],
                "patterns_used": [],
                "impact_analysis": {},
                "summary": "Failed to parse strict response",
                "confidence_score": 0.0,
                "reasoning_trace": [],
                "rag_sources_used": [],
                "validation_warnings": ["JSON parse failed"]
            }
    
    def create_output(self, parsed_data: Dict[str, Any], **kwargs) -> CodeOutput:
        """Create CodeOutput with strict validation"""
        ticket_id = kwargs.get("ticket_id", "UNKNOWN")
        
        # Parse diff hunks
        hunks = []
        for h in parsed_data.get("diff_hunks", []):
            hunks.append(DiffHunk(
                file=h.get("file", "unknown.py"),
                old_start=h.get("old_start", 1),
                old_count=h.get("old_count", 0),
                new_start=h.get("new_start", 1),
                new_count=h.get("new_count", 0),
                content=h.get("content", ""),
                description=h.get("description", "")
            ))
        
        # Parse generated files
        files = []
        for f in parsed_data.get("generated_files", []):
            content = f.get("content", "")
            files.append(GeneratedFile(
                filename=f.get("filename", "generated.py"),
                language=f.get("language", "python"),
                content=content,
                description=f.get("description", ""),
                line_count=f.get("line_count", len(content.split("\n"))),
                is_new=f.get("is_new", True)
            ))
        
        # Parse impact analysis
        impact_data = parsed_data.get("impact_analysis", {})
        impact = ImpactAnalysis(
            affected_classes=impact_data.get("affected_classes", []),
            affected_methods=impact_data.get("affected_methods", []),
            affected_tests=impact_data.get("affected_tests", []),
            breaking_change_risk=impact_data.get("breaking_change_risk", "low"),
            migration_notes=impact_data.get("migration_notes", [])
        )
        
        total_files = len(files) + len(hunks)
        warnings = parsed_data.get("validation_warnings", [])
        
        # Calculate confidence
        base_confidence = parsed_data.get("confidence_score", 0.9)
        if total_files == 0:
            base_confidence = 0.0
        if len(warnings) > 0:
            base_confidence -= 0.1 * len(warnings)
        
        confidence = max(0.0, min(1.0, base_confidence))
        
        return CodeOutput(
            agent_name="CodeGenerator",
            mode=self.mode,
            ticket_id=ticket_id,
            files_modified=parsed_data.get("files_modified", [f.filename for f in files]),
            diff_hunks=hunks,
            generated_files=files,
            patterns_used=parsed_data.get("patterns_used", []),
            impact_analysis=impact,
            summary=parsed_data.get("summary", f"Generated {len(files)} files (strict mode)"),
            quality_metrics=QualityMetrics(
                confidence_score=confidence,
                completeness_score=min(1.0, total_files / 3),
                items_count=total_files,
                has_errors=len(warnings) > 0,
                error_messages=warnings
            ),
            reasoning_trace=ReasoningTrace(
                steps=parsed_data.get("reasoning_trace", []),
                rag_sources_used=parsed_data.get("rag_sources_used", []),
                patterns_matched=parsed_data.get("patterns_used", []),
                decisions_made=[{"mode": "strict", "reason": "Quality gate enforcement"}]
            )
        )
