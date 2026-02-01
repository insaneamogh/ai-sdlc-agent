# AI SDLC Agent

## Overview
An AI-native SDLC (Software Development Lifecycle) orchestration system that automates:
- **Requirement Analysis**: Extract structured requirements from Jira tickets
- **Code Generation**: Generate code based on requirements and existing patterns
- **Test Generation**: Create comprehensive test cases

## Project Architecture

### Backend (Python/FastAPI)
- **Location**: `/app/`
- **Framework**: FastAPI with uvicorn
- **Port**: 8001 (localhost)
- **Entry point**: `app/main.py`
- **Key components**:
  - `app/agents/` - AI agents for requirements, code, and test generation
  - `app/api/routes.py` - API endpoints
  - `app/orchestration/` - LangGraph orchestration
  - `app/services/` - External services (GitHub, Jira, embeddings)
  - `app/vectorstore/` - ChromaDB vector store

### Frontend (React/Vite)
- **Location**: `/ui/`
- **Framework**: React with Vite
- **Port**: 5000 (0.0.0.0)
- **Styling**: Tailwind CSS

## Required Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for LLM access

### Optional
- `JIRA_URL` - Jira instance URL
- `JIRA_EMAIL` - Jira account email
- `JIRA_API_TOKEN` - Jira API token
- `GITHUB_TOKEN` - GitHub personal access token

## Running the Application

The application runs with a single workflow that starts both:
1. Frontend (Vite dev server) on port 5000
2. Backend (FastAPI/Uvicorn) on port 8001

The frontend proxies API calls to the backend via `/api` route.

## Recent Changes
- 2026-02-01: Initial Replit environment setup
  - Configured Vite to run on 0.0.0.0:5000 with allowedHosts enabled
  - Backend runs on localhost:8001
  - Single combined workflow for frontend + backend
