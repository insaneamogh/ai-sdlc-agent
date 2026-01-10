#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
GitHub Service Module

This module provides integration with GitHub API for:
- Fetching repository information
- Retrieving PR details and diffs
- Getting code files for context
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import httpx
from app.config import get_settings
from app.utils.logger import logger


class GitHubPR(BaseModel):
    """Model for a GitHub Pull Request"""
    number: int
    title: str
    description: str
    state: str
    author: str
    base_branch: str
    head_branch: str
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0
    diff: Optional[str] = None


class GitHubFile(BaseModel):
    """Model for a GitHub file"""
    path: str
    content: str
    sha: str
    size: int


class GitHubService:
    """
    Service for interacting with GitHub REST API.
    
    This service handles:
    - Authentication with GitHub
    - Fetching PR details and diffs
    - Retrieving repository files
    
    Example usage:
        service = GitHubService()
        pr = await service.get_pr("org/repo", 42)
    """
    
    def __init__(self):
        """Initialize the GitHub service with configuration"""
        settings = get_settings()
        self.token = settings.github_token
        self.base_url = "https://api.github.com"
        self._client: Optional[httpx.AsyncClient] = None
        
        # Check if GitHub is configured
        self.is_configured = bool(self.token)
        
        if not self.is_configured:
            logger.warning("GitHub service not configured - using mock data")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-SDLC-Agent"
            }
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _parse_repo_url(self, url: str) -> tuple:
        """
        Parse GitHub URL to extract owner and repo.
        
        Args:
            url: GitHub URL (e.g., https://github.com/org/repo)
        
        Returns:
            Tuple of (owner, repo)
        """
        # Handle various URL formats
        url = url.rstrip("/")
        if url.startswith("https://github.com/"):
            parts = url.replace("https://github.com/", "").split("/")
        elif url.startswith("git@github.com:"):
            parts = url.replace("git@github.com:", "").replace(".git", "").split("/")
        else:
            parts = url.split("/")
        
        if len(parts) >= 2:
            return parts[0], parts[1]
        return "", ""
    
    async def get_pr(self, repo: str, pr_number: int) -> GitHubPR:
        """
        Fetch a Pull Request from GitHub.
        
        Args:
            repo: Repository in format "owner/repo" or full URL
            pr_number: PR number
        
        Returns:
            GitHubPR with PR details
        """
        logger.info(f"Fetching GitHub PR: {repo}#{pr_number}")
        
        if not self.is_configured:
            return self._get_mock_pr(pr_number)
        
        # Parse repo if it's a URL
        if "github.com" in repo:
            owner, repo_name = self._parse_repo_url(repo)
            repo = f"{owner}/{repo_name}"
        
        try:
            client = await self._get_client()
            response = await client.get(f"/repos/{repo}/pulls/{pr_number}")
            response.raise_for_status()

            data = response.json()
            return self._parse_pr(data)

        except httpx.HTTPStatusError as e:
            # Propagate a clear error including status and body
            status = e.response.status_code if e.response is not None else ""
            text = e.response.text if e.response is not None else str(e)
            logger.error(f"Failed to fetch PR {repo}#{pr_number}: {status} {text}")
            raise Exception(f"GitHub API error fetching PR {repo}#{pr_number}: {status} {text}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch PR {repo}#{pr_number}: {e}")
            raise Exception(f"GitHub HTTP error fetching PR {repo}#{pr_number}: {e}")
    
    def _parse_pr(self, data: Dict[str, Any]) -> GitHubPR:
        """Parse GitHub API response into GitHubPR model"""
        return GitHubPR(
            number=data.get("number", 0),
            title=data.get("title", ""),
            description=data.get("body", "") or "",
            state=data.get("state", "unknown"),
            author=data.get("user", {}).get("login", "unknown"),
            base_branch=data.get("base", {}).get("ref", "main"),
            head_branch=data.get("head", {}).get("ref", "feature"),
            files_changed=data.get("changed_files", 0),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0)
        )
    
    def _get_mock_pr(self, pr_number: int) -> GitHubPR:
        """Return mock PR data for development/testing"""
        return GitHubPR(
            number=pr_number,
            title=f"feat: Implement user authentication #{pr_number}",
            description="""## Summary
This PR implements the user authentication feature as described in PROJ-123.

## Changes
- Added AuthenticationService class
- Implemented OAuth 2.0 integration
- Added JWT token management
- Created login/logout endpoints

## Testing
- Added unit tests for AuthenticationService
- Added integration tests for OAuth flow
- Manual testing completed

## Checklist
- [x] Code follows project style guidelines
- [x] Tests pass locally
- [x] Documentation updated""",
            state="open",
            author="developer",
            base_branch="main",
            head_branch="feature/authentication",
            files_changed=8,
            additions=450,
            deletions=23,
            diff=self._get_mock_diff()
        )
    
    def _get_mock_diff(self) -> str:
        """Return mock diff for development"""
        return """diff --git a/src/auth/service.py b/src/auth/service.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth/service.py
@@ -0,0 +1,50 @@
+class AuthenticationService:
+    def __init__(self):
+        self._users = {}
+    
+    async def authenticate(self, email: str, password: str):
+        # Validate credentials
+        if not email or not password:
+            return None
+        return User(email=email, is_authenticated=True)
"""
    
    async def get_pr_diff(self, repo: str, pr_number: int) -> str:
        """
        Get the diff for a Pull Request.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
        
        Returns:
            Diff as string
        """
        logger.info(f"Fetching diff for PR: {repo}#{pr_number}")
        
        if not self.is_configured:
            return self._get_mock_diff()
        
        try:
            client = await self._get_client()
            # Request diff format
            headers = {"Accept": "application/vnd.github.v3.diff"}
            response = await client.get(
                f"/repos/{repo}/pulls/{pr_number}",
                headers=headers
            )
            response.raise_for_status()

            return response.text

        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else ""
            text = e.response.text if e.response is not None else str(e)
            logger.error(f"Failed to fetch diff for {repo}#{pr_number}: {status} {text}")
            raise Exception(f"GitHub API error fetching diff for {repo}#{pr_number}: {status} {text}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch diff for {repo}#{pr_number}: {e}")
            raise Exception(f"GitHub HTTP error fetching diff for {repo}#{pr_number}: {e}")
    
    async def _get_default_branch(self, repo: str) -> str:
        """Return the repository default branch name by querying the repo metadata."""
        try:
            client = await self._get_client()
            response = await client.get(f"/repos/{repo}")
            response.raise_for_status()
            data = response.json()
            return data.get("default_branch", "main")
        except Exception:
            return "main"

    async def get_file(
        self,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> Optional[GitHubFile]:
        """
        Get a file from a repository.
        
        Args:
            repo: Repository in format "owner/repo"
            path: File path in repository
            ref: Branch or commit reference
        
        Returns:
            GitHubFile with file content
        """
        logger.info(f"Fetching file: {repo}/{path}@{ref}")
        
        if not self.is_configured:
            return GitHubFile(
                path=path,
                content="# Mock file content\nprint('Hello, World!')",
                sha="abc123",
                size=100
            )
        # If ref is not provided, determine the default branch
        if not ref:
            ref = await self._get_default_branch(repo)
        try:
            client = await self._get_client()
            response = await client.get(
                f"/repos/{repo}/contents/{path}",
                params={"ref": ref}
            )
            response.raise_for_status()

            data = response.json()

            # Decode base64 content
            import base64
            content = base64.b64decode(data.get("content", "")).decode("utf-8")

            return GitHubFile(
                path=data.get("path", path),
                content=content,
                sha=data.get("sha", ""),
                size=data.get("size", 0)
            )

        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else ""
            text = e.response.text if e.response is not None else str(e)
            logger.error(f"Failed to fetch file {repo}/{path}: {status} {text}")
            raise Exception(f"GitHub API error fetching file {repo}/{path}: {status} {text}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch file {repo}/{path}: {e}")
            raise Exception(f"GitHub HTTP error fetching file {repo}/{path}: {e}")
    
    async def list_files(
        self,
        repo: str,
        path: str = "",
        ref: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in a repository directory.
        
        Args:
            repo: Repository in format "owner/repo"
            path: Directory path (empty for root)
            ref: Branch or commit reference
        
        Returns:
            List of file/directory information
        """
        if not self.is_configured:
            return [
                {"name": "src", "type": "dir", "path": "src"},
                {"name": "tests", "type": "dir", "path": "tests"},
                {"name": "README.md", "type": "file", "path": "README.md"},
                {"name": "requirements.txt", "type": "file", "path": "requirements.txt"}
            ]
        # Resolve ref to default branch when not specified
        if not ref:
            ref = await self._get_default_branch(repo)
        try:
            client = await self._get_client()
            response = await client.get(
                f"/repos/{repo}/contents/{path}",
                params={"ref": ref}
            )
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return [
                    {
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "path": item.get("path"),
                        "size": item.get("size", 0)
                    }
                    for item in data
                ]

            # If contents API returned empty or a single file, fall back to the git/trees API for a recursive listing
            tree_resp = await client.get(f"/repos/{repo}/git/trees/{ref}", params={"recursive": "1"})
            try:
                tree_resp.raise_for_status()
                tree_data = tree_resp.json()
                tree = tree_data.get("tree", [])
                # Filter by path prefix if a subpath was requested
                prefix = path.rstrip('/') + '/' if path else ''
                items = []
                for item in tree:
                    item_path = item.get("path", "")
                    if prefix and not item_path.startswith(prefix):
                        continue
                    # Map git tree types to content types used elsewhere
                    items.append({
                        "name": item_path.split('/')[-1],
                        "type": "file" if item.get("type") == "blob" else "dir",
                        "path": item_path,
                        "size": item.get("size", 0)
                    })
                return items
            except httpx.HTTPStatusError:
                return []

        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else ""
            text = e.response.text if e.response is not None else str(e)
            logger.error(f"Failed to list files in {repo}/{path}: {status} {text}")
            raise Exception(f"GitHub API error listing files in {repo}/{path}: {status} {text}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to list files in {repo}/{path}: {e}")
            raise Exception(f"GitHub HTTP error listing files in {repo}/{path}: {e}")

#__________________________GenAI: Generated code ends here______________________________#
