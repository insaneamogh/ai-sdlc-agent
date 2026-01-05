#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
API Tests Module

This module contains tests for the FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AI SDLC Agent is running"
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_health_endpoint(self):
        """Test the API health endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI SDLC Agent"


class TestAnalyzeEndpoints:
    """Tests for analyze endpoints"""
    
    def test_analyze_ticket_basic(self):
        """Test basic ticket analysis"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "ticket_id": "TEST-123",
                "action": "analyze_requirements"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == "TEST-123"
        assert data["status"] == "completed"
        assert "requirements" in data
        assert len(data["requirements"]) > 0
    
    def test_analyze_ticket_full_pipeline(self):
        """Test full pipeline analysis"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "ticket_id": "TEST-456",
                "action": "full_pipeline"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == "TEST-456"
        assert data["action"] == "full_pipeline"
        assert "agents" in data
        # Full pipeline should have multiple agents
        assert len(data["agents"]) >= 2
    
    def test_analyze_ticket_with_github_context(self):
        """Test analysis with GitHub context"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "ticket_id": "TEST-789",
                "action": "generate_code",
                "github_repo": "https://github.com/org/repo",
                "github_pr": "https://github.com/org/repo/pull/42"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == "TEST-789"
    
    def test_analyze_manual_ticket(self):
        """Test manual ticket analysis"""
        response = client.post(
            "/api/v1/analyze/manual",
            json={
                "ticket": {
                    "title": "Test Feature",
                    "description": "Implement a test feature"
                },
                "action": "analyze_requirements"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "MANUAL" in data["ticket_id"]
        assert data["status"] == "completed"


class TestTicketEndpoints:
    """Tests for ticket endpoints"""
    
    def test_get_ticket(self):
        """Test getting ticket details"""
        response = client.get("/api/v1/tickets/PROJ-123")
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == "PROJ-123"
        assert "title" in data
        assert "description" in data
        assert "status" in data


class TestAgentEndpoints:
    """Tests for agent-related endpoints"""
    
    def test_list_agents(self):
        """Test listing available agents"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 3  # RequirementAnalyzer, CodeGenerator, TestGenerator
        
        agent_names = [a["name"] for a in data["agents"]]
        assert "RequirementAnalyzer" in agent_names
        assert "CodeGenerator" in agent_names
        assert "TestGenerator" in agent_names
    
    def test_get_request_status(self):
        """Test getting request status"""
        response = client.get("/api/v1/status/abc123")
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "abc123"
        assert "status" in data


class TestValidation:
    """Tests for input validation"""
    
    def test_analyze_missing_ticket_id(self):
        """Test that missing ticket_id returns error"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "action": "analyze_requirements"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_analyze_invalid_action(self):
        """Test that invalid action returns error"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "ticket_id": "TEST-123",
                "action": "invalid_action"
            }
        )
        assert response.status_code == 422  # Validation error


# ===========================================
# Async Tests (using pytest-asyncio)
# ===========================================

@pytest.mark.asyncio
async def test_async_health_check():
    """Test async health check"""
    # This is a placeholder for async tests
    # In a real scenario, you'd use httpx.AsyncClient
    assert True


# ===========================================
# Fixtures
# ===========================================

@pytest.fixture
def sample_ticket():
    """Fixture for a sample ticket"""
    return {
        "ticket_id": "SAMPLE-001",
        "title": "Sample Feature",
        "description": "This is a sample feature description",
        "acceptance_criteria": "Given... When... Then..."
    }


@pytest.fixture
def sample_requirements():
    """Fixture for sample requirements"""
    return [
        {
            "id": "REQ-001",
            "type": "functional",
            "description": "User authentication",
            "priority": "high"
        },
        {
            "id": "REQ-002",
            "type": "non-functional",
            "description": "Response time < 3s",
            "priority": "medium"
        }
    ]


def test_with_sample_ticket(sample_ticket):
    """Test using sample ticket fixture"""
    assert sample_ticket["ticket_id"] == "SAMPLE-001"
    assert "description" in sample_ticket

#__________________________GenAI: Generated code ends here______________________________#
