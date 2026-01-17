"""
Jira Service Module

This module provides integration with Jira REST API for:
- Fetching ticket details
- Retrieving acceptance criteria
- Getting linked PRs and issues

Supports both Jira Cloud (API v3) and Jira Server (API v2).
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import httpx
import re
from app.config import get_settings
from app.utils.logger import logger


class JiraTicket(BaseModel):
    """Model for a Jira ticket"""
    id: str
    key: str
    title: str
    description: str
    status: str
    issue_type: str
    priority: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    labels: List[str] = []
    linked_issues: List[str] = []
    linked_prs: List[str] = []
    # Additional fields for SDLC agent
    components: List[str] = []
    epic_key: Optional[str] = None
    story_points: Optional[float] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None


class JiraService:
    """
    Service for interacting with Jira REST API.
    
    This service handles:
    - Authentication with Jira (Cloud and Server)
    - Fetching ticket details
    - Parsing ticket fields including ADF (Atlassian Document Format)
    
    Example usage:
        service = JiraService()
        ticket = await service.get_ticket("PROJ-123")
    """
    
    # Common custom field IDs for acceptance criteria across Jira instances
    ACCEPTANCE_CRITERIA_FIELDS = [
        "customfield_10001",  # Common default
        "customfield_10100",  # Another common default
        "customfield_10200",  # Jira Software
        "customfield_10300",  # Some instances
        "customfield_10400",  # Some instances
        "customfield_10014",  # Jira Cloud default for AC
        "customfield_10015",  # Alternative
    ]
    
    # Story points custom field IDs
    STORY_POINTS_FIELDS = [
        "customfield_10002",
        "customfield_10004",
        "customfield_10016",
        "customfield_10026",
    ]
    
    def __init__(self):
        """Initialize the Jira service with configuration"""
        settings = get_settings()
        self.base_url = settings.jira_url
        self.email = settings.jira_email
        self.api_token = settings.jira_api_token
        self._client: Optional[httpx.AsyncClient] = None
        
        # Detect if this is Jira Cloud or Server
        self.is_cloud = self.base_url and "atlassian.net" in self.base_url
        
        # Check if Jira is configured
        self.is_configured = bool(
            self.base_url and self.email and self.api_token
        )
        
        if not self.is_configured:
            logger.warning("Jira service not configured - set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env")
        else:
            logger.info(f"Jira service configured for {'Cloud' if self.is_cloud else 'Server'}: {self.base_url}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Jira Cloud uses Basic Auth with email:api_token
            # Jira Server may use different auth methods
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.email, self.api_token),
                headers=headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the Jira connection and return server info.
        
        Returns:
            Dict with connection status and server info
        """
        if not self.is_configured:
            return {"connected": False, "error": "Jira not configured"}
        
        try:
            client = await self._get_client()
            # Use API v2 for server info as it's more compatible
            response = await client.get("/rest/api/2/serverInfo")
            response.raise_for_status()
            
            data = response.json()
            return {
                "connected": True,
                "server_title": data.get("serverTitle", "Unknown"),
                "version": data.get("version", "Unknown"),
                "deployment_type": data.get("deploymentType", "Unknown"),
                "base_url": self.base_url
            }
        except httpx.HTTPStatusError as e:
            return {
                "connected": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    async def get_ticket(self, ticket_id: str) -> JiraTicket:
        """
        Fetch a ticket from Jira.
        
        Args:
            ticket_id: The Jira ticket key (e.g., PROJ-123)
        
        Returns:
            JiraTicket with ticket details
        """
        logger.info(f"Fetching Jira ticket: {ticket_id}")
        
        if not self.is_configured:
            logger.warning(f"Jira not configured, returning mock data for {ticket_id}")
            return self._get_mock_ticket(ticket_id)
        
        try:
            client = await self._get_client()
            
            # Use API v3 for Cloud, v2 for Server
            api_version = "3" if self.is_cloud else "2"
            
            response = await client.get(
                f"/rest/api/{api_version}/issue/{ticket_id}",
                params={
                    "expand": "renderedFields,names",
                    "fields": "*all"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_ticket(data)
            
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 404:
                logger.error(f"Ticket {ticket_id} not found in Jira")
                raise ValueError(f"Ticket {ticket_id} not found in Jira")
            elif status == 401:
                logger.error("Jira authentication failed - check credentials")
                raise ValueError("Jira authentication failed - check JIRA_EMAIL and JIRA_API_TOKEN")
            elif status == 403:
                logger.error(f"No permission to access ticket {ticket_id}")
                raise ValueError(f"No permission to access ticket {ticket_id}")
            else:
                logger.error(f"Jira API error: {status} - {e.response.text[:200]}")
                raise ValueError(f"Jira API error: {status}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch ticket {ticket_id}: {e}")
            raise ValueError(f"Failed to connect to Jira: {e}")
    
    def _parse_adf_to_text(self, adf: Any) -> str:
        """
        Parse Atlassian Document Format (ADF) to plain text.
        
        ADF is used in Jira Cloud API v3 for rich text fields.
        """
        if adf is None:
            return ""
        
        if isinstance(adf, str):
            return adf
        
        if not isinstance(adf, dict):
            return str(adf)
        
        # ADF structure: {"type": "doc", "content": [...]}
        content = adf.get("content", [])
        text_parts = []
        
        for node in content:
            text_parts.append(self._parse_adf_node(node))
        
        return "\n".join(text_parts)
    
    def _parse_adf_node(self, node: Dict[str, Any]) -> str:
        """Parse a single ADF node recursively"""
        if not isinstance(node, dict):
            return str(node) if node else ""
        
        node_type = node.get("type", "")
        
        if node_type == "text":
            return node.get("text", "")
        
        if node_type == "hardBreak":
            return "\n"
        
        if node_type == "paragraph":
            content = node.get("content", [])
            return "".join(self._parse_adf_node(n) for n in content) + "\n"
        
        if node_type == "heading":
            content = node.get("content", [])
            level = node.get("attrs", {}).get("level", 1)
            text = "".join(self._parse_adf_node(n) for n in content)
            return f"{'#' * level} {text}\n"
        
        if node_type == "bulletList":
            items = node.get("content", [])
            return "\n".join(f"• {self._parse_adf_node(item)}" for item in items)
        
        if node_type == "orderedList":
            items = node.get("content", [])
            return "\n".join(f"{i+1}. {self._parse_adf_node(item)}" for i, item in enumerate(items))
        
        if node_type == "listItem":
            content = node.get("content", [])
            return "".join(self._parse_adf_node(n) for n in content).strip()
        
        if node_type == "codeBlock":
            content = node.get("content", [])
            code = "".join(self._parse_adf_node(n) for n in content)
            return f"```\n{code}\n```"
        
        if node_type == "blockquote":
            content = node.get("content", [])
            text = "".join(self._parse_adf_node(n) for n in content)
            return f"> {text}"
        
        # For unknown types, try to extract content recursively
        if "content" in node:
            return "".join(self._parse_adf_node(n) for n in node["content"])
        
        return ""
    
    def _extract_acceptance_criteria(self, fields: Dict[str, Any], rendered_fields: Dict[str, Any]) -> Optional[str]:
        """
        Extract acceptance criteria from various possible locations.
        
        Checks:
        1. Known custom field IDs
        2. Description section with "Acceptance Criteria" header
        3. Rendered fields for HTML content
        """
        # Check custom fields
        for field_id in self.ACCEPTANCE_CRITERIA_FIELDS:
            if field_id in fields and fields[field_id]:
                value = fields[field_id]
                if isinstance(value, dict):
                    return self._parse_adf_to_text(value)
                return str(value)
        
        # Check rendered fields (HTML)
        for field_id in self.ACCEPTANCE_CRITERIA_FIELDS:
            if field_id in rendered_fields and rendered_fields[field_id]:
                # Strip HTML tags for plain text
                html = rendered_fields[field_id]
                return re.sub(r'<[^>]+>', '', html).strip()
        
        # Try to extract from description
        description = fields.get("description", "")
        if isinstance(description, dict):
            description = self._parse_adf_to_text(description)
        
        if description:
            # Look for "Acceptance Criteria" section
            patterns = [
                r"(?:Acceptance Criteria|AC|Given.*When.*Then)[\s:]*(.+?)(?=\n\n|\Z)",
                r"(?:##?\s*Acceptance Criteria)[\s:]*(.+?)(?=\n##|\Z)",
            ]
            for pattern in patterns:
                match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
        
        return None
    
    def _parse_ticket(self, data: Dict[str, Any]) -> JiraTicket:
        """Parse Jira API response into JiraTicket model"""
        fields = data.get("fields", {})
        rendered_fields = data.get("renderedFields", {})
        
        # Parse description (may be ADF in Cloud API v3)
        description = fields.get("description", "")
        if isinstance(description, dict):
            description = self._parse_adf_to_text(description)
        elif description is None:
            description = ""
        
        # Extract acceptance criteria
        acceptance_criteria = self._extract_acceptance_criteria(fields, rendered_fields)
        
        # Extract linked PRs from development field or links
        linked_prs = []
        linked_issues = []
        if "issuelinks" in fields:
            for link in fields.get("issuelinks", []):
                if "outwardIssue" in link:
                    linked_issues.append(link["outwardIssue"]["key"])
                if "inwardIssue" in link:
                    linked_issues.append(link["inwardIssue"]["key"])
        
        # Extract components
        components = [c.get("name", "") for c in fields.get("components", [])]
        
        # Extract epic key
        epic_key = None
        for field_id in ["customfield_10008", "customfield_10014", "parent"]:
            if field_id in fields and fields[field_id]:
                epic_data = fields[field_id]
                if isinstance(epic_data, dict):
                    epic_key = epic_data.get("key")
                elif isinstance(epic_data, str):
                    epic_key = epic_data
                break
        
        # Extract story points
        story_points = None
        for field_id in self.STORY_POINTS_FIELDS:
            if field_id in fields and fields[field_id] is not None:
                try:
                    story_points = float(fields[field_id])
                    break
                except (ValueError, TypeError):
                    pass
        
        # Extract assignee and reporter
        assignee = None
        if fields.get("assignee"):
            assignee = fields["assignee"].get("displayName") or fields["assignee"].get("emailAddress")
        
        reporter = None
        if fields.get("reporter"):
            reporter = fields["reporter"].get("displayName") or fields["reporter"].get("emailAddress")
        
        return JiraTicket(
            id=data.get("id", ""),
            key=data.get("key", ""),
            title=fields.get("summary", ""),
            description=description,
            status=fields.get("status", {}).get("name", "Unknown"),
            issue_type=fields.get("issuetype", {}).get("name", "Task"),
            priority=fields.get("priority", {}).get("name") if fields.get("priority") else None,
            acceptance_criteria=acceptance_criteria,
            labels=fields.get("labels", []),
            linked_issues=linked_issues,
            linked_prs=linked_prs,
            components=components,
            epic_key=epic_key,
            story_points=story_points,
            assignee=assignee,
            reporter=reporter
        )
    
    def _get_mock_ticket(self, ticket_id: str) -> JiraTicket:
        """Return mock ticket data for development/testing"""
        return JiraTicket(
            id="10001",
            key=ticket_id,
            title=f"Implement User Authentication - {ticket_id}",
            description="""As a user, I want to be able to log in to the application 
so that I can access my personalized dashboard.

The authentication system should:
- Support email/password login
- Integrate with OAuth 2.0 providers (Google, GitHub)
- Implement secure session management
- Support multi-factor authentication (MFA)

Technical Requirements:
- Use JWT tokens for session management
- Implement rate limiting on login attempts
- Log all authentication events for audit""",
            status="In Progress",
            issue_type="Story",
            priority="High",
            acceptance_criteria="""Given a user with valid credentials
When they submit the login form
Then they should be authenticated and redirected to dashboard

Given a user with invalid credentials
When they submit the login form
Then they should see an error message

Given a user with MFA enabled
When they enter correct password
Then they should be prompted for MFA code""",
            labels=["authentication", "security", "mvp"],
            linked_issues=["PROJ-100", "PROJ-101"],
            linked_prs=["https://github.com/org/repo/pull/42"]
        )
    
    async def search_tickets(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[JiraTicket]:
        """
        Search for tickets using JQL.
        
        Args:
            jql: Jira Query Language string
            max_results: Maximum number of results
        
        Returns:
            List of matching tickets
        """
        logger.info(f"Searching Jira with JQL: {jql}")
        
        if not self.is_configured:
            # Return mock results
            return [self._get_mock_ticket(f"PROJ-{i}") for i in range(1, 4)]
        
        try:
            client = await self._get_client()
            response = await client.get(
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "maxResults": max_results
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                self._parse_ticket(issue)
                for issue in data.get("issues", [])
            ]
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to search tickets: {e}")
            return []
    
    async def get_ticket_comments(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Get comments for a ticket.
        
        Args:
            ticket_id: The Jira ticket key
        
        Returns:
            List of comments
        """
        if not self.is_configured:
            return [
                {
                    "author": "developer@example.com",
                    "body": "Started implementation of OAuth integration",
                    "created": "2024-01-15T10:30:00Z"
                }
            ]
        
        try:
            client = await self._get_client()
            response = await client.get(
                f"/rest/api/3/issue/{ticket_id}/comment"
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("comments", [])
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get comments for {ticket_id}: {e}")
            return []
