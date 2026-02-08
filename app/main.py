
"""
FastAPI Application Entry Point

This is the main entry point for the AI SDLC Agent API.
It sets up the FastAPI application, middleware, and routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings, validate_settings
from app.api.routes import router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting AI SDLC Agent...")
    
    # Validate settings
    validation = validate_settings()
    if not validation["valid"]:
        logger.warning(f"⚠️ Missing required settings: {validation['missing']}")
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.info(f"ℹ️ {warning}")
    
    logger.info("✅ AI SDLC Agent started successfully!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down AI SDLC Agent...")


# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description="""
## AI SDLC Agent API

An AI-native SDLC orchestration system that automates:
- **Requirement Analysis**: Extract structured requirements from Jira tickets
- **Code Generation**: Generate code based on requirements and existing patterns
- **Test Generation**: Create comprehensive test cases

### Key Features
- Multi-agent orchestration using LangGraph
- RAG-powered context grounding
- Jira and GitHub integration
- Real-time agent status tracking

### Available Actions
- `analyze_requirements` - Extract requirements from ticket
- `generate_code` - Generate code based on requirements
- `generate_tests` - Create test cases
- `full_pipeline` - Run all agents in sequence
    """,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware (allows frontend to call API)
cors_origins_raw = settings.cors_origins.strip()
if cors_origins_raw == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint - basic info about the API.
    """
    return {
        "message": "AI SDLC Agent is running",
        "version": settings.api_version,
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API.
    """
    return {
        "status": "healthy",
        "service": "AI SDLC Agent",
        "version": settings.api_version
    }

