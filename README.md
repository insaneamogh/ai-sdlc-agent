# 🚀 AI SDLC Agent

An AI-native SDLC orchestration system that automates requirement analysis, code generation, and test creation using real SDLC data from Jira and GitHub.

## 🎯 What This Project Is

**This is NOT:**
- A ChatGPT wrapper
- A code autocomplete tool like Codex
- A general chatbot like Gemini

**This IS:**
- An AI agent fabric that automates requirement analysis, code generation, and test creation
- A multi-agent orchestration system using LangGraph
- A RAG-powered system grounded in real SDLC context

---

## 📊 State Machine Diagrams

### 1. UI State Machine (Frontend Flow)

```mermaid
stateDiagram-v2
    [*] --> InputScreen: App Load
    
    InputScreen --> Validating: Submit Form
    Validating --> InputScreen: Validation Failed
    Validating --> Executing: Validation Passed
    
    Executing --> AgentProgress: API Call Started
    AgentProgress --> AgentProgress: Agent Updates
    AgentProgress --> ResultScreen: All Agents Complete
    AgentProgress --> ErrorScreen: API Error
    
    ResultScreen --> InputScreen: New Pipeline
    ErrorScreen --> InputScreen: Retry
    
    state InputScreen {
        [*] --> EnterKeys
        EnterKeys --> EnterTicket: Keys Valid
        EnterTicket --> Ready: Ticket Entered
    }
    
    state AgentProgress {
        [*] --> RequirementAgent
        RequirementAgent --> CodeAgent
        CodeAgent --> TestAgent
        TestAgent --> [*]
    }
```

### 2. Backend Pipeline State Machine (LangGraph Orchestration)

```mermaid
stateDiagram-v2
    [*] --> RequirementAnalyzer: Start Pipeline
    
    RequirementAnalyzer --> ActionDecision: Analysis Complete
    
    state ActionDecision <<choice>>
    ActionDecision --> [*]: action = analyze_requirements
    ActionDecision --> CodeGenerator: action = generate_code
    ActionDecision --> TestGenerator: action = generate_tests  
    ActionDecision --> CodeGenerator: action = full_pipeline
    
    CodeGenerator --> CodeDecision: Code Generated
    
    state CodeDecision <<choice>>
    CodeDecision --> [*]: action = generate_code
    CodeDecision --> TestGenerator: action = full_pipeline
    
    TestGenerator --> [*]: Tests Generated
    
    note right of RequirementAnalyzer
        Extracts structured requirements
        from ticket description
    end note
    
    note right of CodeGenerator
        Generates code based on
        requirements + RAG context
    end note
    
    note right of TestGenerator
        Creates unit/integration tests
        for generated code
    end note
```

### 3. File Connection Diagram (System Architecture)

```mermaid
graph TB
    subgraph "Frontend Layer (ui/)"
        A[main.jsx] --> B[App.jsx]
        B --> C[api.js]
        B --> D[ErrorBoundary.jsx]
        E[index.css] --> B
    end
    
    subgraph "API Layer (app/api/)"
        F[main.py] --> G[routes.py]
        G --> H[config.py]
    end
    
    subgraph "Services Layer (app/services/)"
        I[github_service.py]
        J[jira_service.py]
        K[embedding_service.py]
    end
    
    subgraph "Orchestration Layer (app/orchestration/)"
        L[graph.py]
    end
    
    subgraph "Agents Layer (app/agents/)"
        M[requirement_agent.py]
        N[code_agent.py]
        O[test_agent.py]
    end
    
    subgraph "Data Layer (app/vectorstore/)"
        P[chroma_store.py]
    end
    
    subgraph "Schemas (app/schemas/)"
        Q[models.py]
    end
    
    subgraph "Utilities (app/utils/)"
        R[logger.py]
    end
    
    C -->|HTTP POST /api/v1/analyze| G
    G --> I
    G --> J
    G --> L
    L --> M
    L --> N
    L --> O
    M --> K
    N --> K
    O --> K
    K --> P
    M --> Q
    N --> Q
    O --> Q
    G --> R
    L --> R
    
    style A fill:#61dafb
    style B fill:#61dafb
    style F fill:#009688
    style G fill:#009688
    style L fill:#ff9800
    style M fill:#4caf50
    style N fill:#4caf50
    style O fill:#4caf50
    style P fill:#9c27b0
```

### 4. API Request Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    participant UI as React UI
    participant API as FastAPI
    participant GH as GitHubService
    participant Orch as SDLCOrchestrator
    participant RA as RequirementAgent
    participant CA as CodeAgent
    participant TA as TestAgent
    participant VS as VectorStore
    
    UI->>API: POST /api/v1/analyze
    API->>GH: Fetch repo context (optional)
    GH-->>API: Repository files
    
    API->>Orch: run(ticket_data, action)
    
    Orch->>RA: analyze(ticket)
    RA->>VS: search_similar_tickets()
    VS-->>RA: RAG context
    RA-->>Orch: requirements[]
    
    alt action = generate_code or full_pipeline
        Orch->>CA: generate(requirements)
        CA->>VS: search_similar_code()
        VS-->>CA: Code patterns
        CA-->>Orch: generated_code
    end
    
    alt action = generate_tests or full_pipeline
        Orch->>TA: generate(code, requirements)
        TA-->>Orch: generated_tests
    end
    
    Orch-->>API: final_state
    API-->>UI: JSON response
```

### 5. Data Flow Diagram

```mermaid
flowchart LR
    subgraph Input
        A[Jira Ticket]
        B[GitHub Repo]
        C[API Keys]
    end
    
    subgraph Processing
        D[FastAPI Gateway]
        E[LangGraph Orchestrator]
        F[AI Agents]
        G[Vector Store]
    end
    
    subgraph Output
        H[Requirements JSON]
        I[Generated Code]
        J[Test Suite]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F <--> G
    F --> H
    F --> I
    F --> J
    
    style D fill:#009688
    style E fill:#ff9800
    style F fill:#4caf50
    style G fill:#9c27b0
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Input Screen│  │Agent Status │  │Results View │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Gateway                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Requirement  │ │    Code      │ │    Test      │        │
│  │   Agent      │→│   Agent      │→│   Agent      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Vector Store (ChromaDB / FAISS)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  Jira   │  │   PRs   │  │  Code   │  │  Tests  │        │
│  │ Tickets │  │         │  │  Diffs  │  │         │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| API | FastAPI | REST endpoints |
| Orchestration | LangGraph | Multi-agent workflows |
| Vector DB | ChromaDB | RAG context storage |
| LLM | GPT-4o/Claude | AI reasoning |
| Integrations | Jira API, GitHub API | Data sources |

## 📁 Project Structure

```
ai-sdlc-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── requirement_agent.py  # Requirement extraction
│   │   ├── code_agent.py         # Code generation
│   │   └── test_agent.py         # Test generation
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── graph.py            # LangGraph workflow
│   ├── services/
│   │   ├── __init__.py
│   │   ├── jira_service.py     # Jira integration
│   │   ├── github_service.py   # GitHub integration
│   │   └── embedding_service.py # Text embeddings
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   └── chroma_store.py     # Vector database
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py           # Pydantic models
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # Logging utility
├── ui/                         # React Frontend
│   ├── src/
│   │   ├── main.jsx           # React entry point
│   │   ├── App.jsx            # Main component
│   │   ├── api.js             # API client
│   │   ├── ErrorBoundary.jsx  # Error handling
│   │   └── index.css          # Styles
│   ├── package.json
│   └── vite.config.js
├── tests/
│   ├── __init__.py
│   └── test_api.py             # API tests
├── data/
│   └── sample_tickets.json     # Sample data
├── .env.example                # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-sdlc-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows (CMD)
   venv\Scripts\activate
   
   # Windows (PowerShell) - if script execution is disabled:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   venv\Scripts\Activate.ps1
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY and GITHUB_TOKEN
   ```

5. **Run the backend server**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

6. **Run the frontend (in a new terminal)**
   ```bash
   cd ui
   npm install
   npm run dev
   ```

7. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

### Windows PowerShell Script Execution Error

If you see this error:
```
File cannot be loaded because running scripts is disabled on this system
```

Run this command in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Analyze Ticket
```bash
POST /api/v1/analyze
{
  "ticket_id": "PROJ-123",
  "action": "full_pipeline"
}
```

### Manual Analysis (without Jira)
```bash
POST /api/v1/analyze/manual
{
  "ticket": {
    "title": "Implement authentication",
    "description": "User login feature..."
  },
  "action": "analyze_requirements"
}
```

### List Agents
```bash
GET /api/v1/agents
```

### Get GitHub File
```bash
POST /api/v1/github/file
{
  "repo": "owner/repo",
  "path": "src/main.py"
}
```

## 🤖 Agents

### 1. Requirement Analyzer Agent
- **Input**: Jira ticket description, acceptance criteria
- **Output**: Structured requirements (functional, non-functional, constraints)
- **Features**: Edge case identification, priority assignment

### 2. Code Generator Agent
- **Input**: Structured requirements, RAG context
- **Output**: Code snippets, diff patches
- **Features**: Pattern matching, coding standards compliance

### 3. Test Generator Agent
- **Input**: Generated code, requirements
- **Output**: Unit tests, integration tests
- **Features**: Edge case coverage, framework matching

## 🔄 Workflow

```mermaid
graph TD
    START([Start]) --> RA[Requirement Analyzer]
    RA --> Decision{Action Type?}
    Decision -->|analyze_requirements| END1([End])
    Decision -->|generate_code| CG[Code Generator]
    Decision -->|generate_tests| TG[Test Generator]
    Decision -->|full_pipeline| CG
    CG --> Decision2{Continue?}
    Decision2 -->|full_pipeline| TG
    Decision2 -->|generate_code only| END2([End])
    TG --> END3([End])
```

## 🔐 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `GITHUB_TOKEN` | GitHub personal access token | Yes |
| `JIRA_URL` | Jira instance URL | No |
| `JIRA_EMAIL` | Jira account email | No |
| `JIRA_API_TOKEN` | Jira API token | No |
| `DEBUG` | Enable debug mode | No |
| `LOG_LEVEL` | Logging level | No |

### Secrets & Security

- NEVER commit secrets or `.env` files to version control. This repository's `.gitignore` already excludes `.env` files.
- Local workflow: copy `.env.example` to `.env` and add your real secret values locally only. Do NOT commit the `.env` file.
   ```bash
   cp .env.example .env
   # edit .env locally and paste your keys (DO NOT commit)
   ```
- CI / Deployment: store secrets in your platform's secret store (GitHub Actions Secrets, Azure Key Vault, AWS Secrets Manager, etc.) and inject them as environment variables at runtime.
- Example (GitHub Actions):
   ```yaml
   env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```
- Rotate tokens regularly and restrict scopes. For `GITHUB_TOKEN` prefer least-privilege PAT scopes or use a deploy key for read-only access.
- Audit your repo for accidental secrets before pushing: `git diff --staged` and `git log -p`.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py
```

## 📊 Observability

The system includes:
- Structured logging with loguru
- Token usage tracking
- Execution time monitoring
- Agent status tracking

## 🎯 Key Differentiators

| Feature | Traditional Tools | AI SDLC Agent |
|---------|------------------|---------------|
| Context | None | RAG-powered |
| Workflow | Single prompt | Multi-agent orchestration |
| Grounding | Hallucination-prone | SDLC data grounded |
| Inspection | Black box | LangGraph inspectable |

## ⚠️ Known Issues & Fixes

### ChromaDB on Windows
ChromaDB requires Visual C++ Build Tools on Windows. If you see a build error:
1. Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Uncomment `chromadb>=0.4.0` in `requirements.txt`
3. Run `pip install chromadb`

On Mac/Linux, ChromaDB installs without issues.

### PowerShell Script Execution
If virtual environment activation fails in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🆕 Recent Enhancements

### Backend Improvements

#### LangGraph State Checkpointing
The orchestration layer now supports state persistence and workflow resume:
- **Thread-based execution**: Each workflow runs with a unique `thread_id` for tracking
- **State checkpointing**: Workflow state is persisted using `MemorySaver`
- **Resume capability**: Interrupted workflows can be resumed from last checkpoint
- **State inspection**: Query current state and history via API

#### Streaming API with Server-Sent Events (SSE)
Real-time progress updates during pipeline execution:
- **`POST /api/v1/analyze/stream`**: Stream analysis with real-time events
- **Event types**: `workflow_start`, `node_start`, `node_complete`, `workflow_complete`
- **Progress tracking**: Monitor each agent's execution in real-time

#### New API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analyze/stream` | POST | Stream analysis with SSE |
| `/api/v1/workflow/{thread_id}/state` | GET | Get current workflow state |
| `/api/v1/workflow/{thread_id}/history` | GET | Get state history |
| `/api/v1/workflow/resume` | POST | Resume paused workflow |
| `/api/v1/workflow/diagram` | GET | Get Mermaid diagram |

#### Enhanced Artifact Schemas
New comprehensive schemas for artifact management:
- **`DiffArtifact`**: Enhanced diff with reasoning traces, RAG sources, impact analysis
- **`StateDiagramArtifact`**: State machine diagram generation support
- **`ArtifactBundle`**: Complete bundle aggregating all pipeline outputs
- **`CodeArtifact`/`TestArtifact`**: Enhanced with confidence scores and traceability

### Frontend Components

#### WorkflowVisualizer
Real-time workflow progress visualization:
- Visual graph showing node states (pending, running, completed, error)
- Event timeline with filtering
- State inspector panel for debugging
- Progress bar with overall completion percentage

#### CodeArtifact
Enhanced code display component:
- Syntax highlighting with line numbers
- Confidence badges and AI generation indicators
- Expandable reasoning trace panel
- RAG source attribution
- Copy/download actions
- Diff view toggle support

#### TestSuiteMatrix
Interactive test matrix UI:
- Coverage summary gauges (method, branch, line, assertion density)
- Expandable test rows with code preview
- Test type and status filtering
- Requirement traceability links
- Assertion count tracking

### Usage Examples

#### Streaming Analysis
```javascript
import { analyzeStream } from './api';

const cleanup = analyzeStream(
  {
    ticket_id: 'PROJ-123',
    action: 'full_pipeline',
    github_repo: 'owner/repo'
  },
  (event, eventType) => {
    console.log(`${eventType}:`, event);
  },
  (error) => console.error(error),
  () => console.log('Complete!')
);

// To cancel: cleanup();
```

#### Workflow State Management
```javascript
import { getWorkflowState, resumeWorkflow } from './api';

// Get current state
const state = await getWorkflowState('thread-123');

// Resume interrupted workflow
const result = await resumeWorkflow('thread-123');
```

## 🛣️ Roadmap

- [x] FastAPI backend with LangGraph orchestration
- [x] React frontend with Vite
- [x] GitHub integration
- [x] Streaming responses with SSE
- [x] LangGraph state checkpointing
- [x] Enhanced UI components (WorkflowVisualizer, CodeArtifact, TestSuiteMatrix)
- [x] Enhanced artifact schemas
- [ ] Full Jira integration
- [ ] ChromaDB vector store integration
- [ ] Docker deployment
- [ ] Webhook support
- [ ] Strategy pattern for strict/standard agents
- [ ] Quality-based conditional routing

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines first.

---

**Interview Positioning:**

> "I built an AI-native SDLC agent fabric that integrates Jira and GitHub, uses RAG for context grounding, and LangGraph for multi-agent orchestration across requirement analysis, code generation, and testing."
