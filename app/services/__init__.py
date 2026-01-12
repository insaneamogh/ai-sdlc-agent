"""
Services Package

This package contains external service integrations:
- JiraService: Integration with Jira API
- GitHubService: Integration with GitHub API
- EmbeddingService: Text embedding generation
"""

from app.services.jira_service import JiraService
from app.services.github_service import GitHubService
from app.services.embedding_service import EmbeddingService

__all__ = ["JiraService", "GitHubService", "EmbeddingService"]
