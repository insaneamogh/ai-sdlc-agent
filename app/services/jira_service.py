"""
Jira Service Module

This module provides integration with Jira REST API for:
- Fetching ticket details
- Retrieving acceptance criteria
- Getting linked PRs and issues
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import httpx
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


class JiraService:
    """
    Service for interacting with Jira REST API.
    
    This service handles:
    - Authentication with Jira
    - Fetching ticket details
    - Parsing ticket fields
    
    Example usage:
        service = JiraService()
        ticket = await service.get_ticket("PROJ-123")
    """
    
    def __init__(self):
        """Initialize the Jira service with configuration"""
        settings = get_settings()
        self.base_url = settings.jira_url
        self.email = settings.jira_email
        self.api_token = settings.jira_api_token
        self._client: Optional[httpx.AsyncClient] = None
        
        # Check if Jira is configured
        self.is_configured = bool(
            self.base_url and self.email and self.api_token
        )
        
        if not self.is_configured:
            logger.warning("Jira service not configured - using mock data")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"}
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
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
            return self._get_mock_ticket(ticket_id)
        
        try:
            client = await self._get_client()
            response = await client.get(
                f"/rest/api/3/issue/{ticket_id}",
                params={"expand": "renderedFields"}
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_ticket(data)
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch ticket {ticket_id}: {e}")
            # Return mock data on error for development
            return self._get_mock_ticket(ticket_id)
    
    def _parse_ticket(self, data: Dict[str, Any]) -> JiraTicket:
        """Parse Jira API response into JiraTicket model"""
        fields = data.get("fields", {})
        
        # Extract acceptance criteria from custom field or description
        acceptance_criteria = None
        # Common custom field names for acceptance criteria
        for field_name in ["customfield_10001", "customfield_10100", "acceptance_criteria"]:
            if field_name in fields and fields[field_name]:
                acceptance_criteria = fields[field_name]
                break
        
        # Extract linked PRs from development field or links
        linked_prs = []
        if "issuelinks" in fields:
            for link in fields["issuelinks"]:
                if "outwardIssue" in link:
                    linked_prs.append(link["outwardIssue"]["key"])
        
        return JiraTicket(
            id=data.get("id", ""),
            key=data.get("key", ""),
            title=fields.get("summary", ""),
            description=fields.get("description", "") or "",
            status=fields.get("status", {}).get("name", "Unknown"),
            issue_type=fields.get("issuetype", {}).get("name", "Task"),
            priority=fields.get("priority", {}).get("name"),
            acceptance_criteria=acceptance_criteria,
            labels=fields.get("labels", []),
            linked_issues=[],
            linked_prs=linked_prs
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
