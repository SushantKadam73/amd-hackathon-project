# GRC Platform Architecture Design

**Date:** June 17, 2026
**Purpose:** Comprehensive architecture for Governance, Risk, and Compliance platform

---

## 1. High-Level System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GRC Platform Architecture                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Streamlit   │    │   FastAPI     │    │  PostgreSQL   │               │
│  │   Frontend    │◄──►│   Backend     │◄──►│  + pgvector   │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         │                   │                   │                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Chat UI    │    │  Agent Engine │    │  Document    │               │
│  │   RAG Query  │    │  (Agno)       │    │  Storage     │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         │                   │                   │                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │  Dashboard   │    │  Guardrails   │    │  Vector      │               │
│  │  Reports     │    │  Human-in-   │    │  Embeddings  │               │
│  │  Analytics   │    │  the-Loop    │    │  (NVIDIA)    │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                        │
│         │                   │                   │                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │  Audit Log   │    │  LLM Router   │    │  Compliance  │               │
│  │  Viewer      │    │  Dev/Prod     │    │  Knowledge   │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Data Flow:
1. User interacts with Streamlit Frontend
2. Requests routed through FastAPI Backend
3. Agent Engine processes with Agno library
4. PostgreSQL stores structured data + pgvector for embeddings
5. LLM Router selects appropriate model (OpenRouter dev / Ollama prod)
6. Guardrails ensure compliance and security
```

---

## 2. Component Breakdown with Responsibilities

### 2.1 Presentation Layer (Streamlit Frontend)

**Components:**
- **Dashboard Module**: Risk scores, compliance status, framework mapping overview
- **Chat Interface**: GRC chatbot with RAG capabilities
- **Control Library Manager**: CRUD operations for frameworks/controls
- **Evidence Manager**: Upload, map, and weight evidence artifacts
- **Gap Analysis Viewer**: Visual gap reports and risk heatmaps
- **Audit Log Viewer**: Searchable audit trail with filters

**Responsibilities:**
- User interface rendering and interaction
- Data visualization (charts, tables, heatmaps)
- Form submissions and file uploads
- Real-time updates via WebSocket connections
- Responsive design for desktop deployment

### 2.2 Business Logic Layer (FastAPI Backend)

**Components:**
- **Framework Service**: Framework CRUD and versioning
- **Control Mapping Service**: Cross-framework mapping logic
- **Evidence Service**: Artifact processing and weightage calculation
- **Gap Analysis Service**: Gap detection and risk scoring algorithms
- **Review Workflow Service**: Approve/reject workflows with notifications
- **Audit Service**: Comprehensive logging of all operations
- **Agent Orchestration Service**: Manages Agno agent lifecycle

**Responsibilities:**
- API endpoint handling and request validation
- Business rule enforcement
- Transaction management
- Service coordination and error handling
- Authentication and authorization

### 2.3 AI/ML Layer (Agent System)

**Components:**
- **Agent Engine**: Agno-based agents with memory and knowledge
- **Guardrails Manager**: Input/output validation and compliance checks
- **Human-in-the-Loop Interface**: Review queues and approval workflows
- **RAG System**: Retrieval-Augmented Generation for compliance knowledge
- **LLM Router**: Dynamic model selection (OpenRouter/Ollama)
- **Embedding Service**: NVIDIA Llama Nemotron Embed VL 1B V2 integration

**Responsibilities:**
- Natural language understanding and generation
- Evidence analysis and control mapping suggestions
- Risk assessment automation
- Knowledge retrieval and synthesis
- Compliance validation of AI outputs

### 2.4 Data Layer

**Components:**
- **PostgreSQL Database**: Structured data storage
- **pgvector Extension**: Vector similarity search
- **Document Storage**: File system/blob storage for evidence artifacts
- **Cache Layer**: Redis for session management and frequent queries

**Responsibilities:**
- Data persistence and retrieval
- Vector similarity search for RAG
- Transaction integrity
- Data archival and retention
- Backup and recovery

### 2.5 Integration Layer

**Components:**
- **Document Parser**: Multi-format file processing (PDF, images, DOCX)
- **External System Connectors**: SIEM, ticketing systems, directories
- **Webhook Manager**: Event notifications and integrations
- **Export Service**: Report generation (PDF, Excel, JSON)

**Responsibilities:**
- File format detection and parsing
- External system integration
- Event-driven notifications
- Data export and formatting

---

## 3. Database Schema Design

### 3.1 Core Entities

```sql
-- Framework Management
CREATE TABLE frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    version_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE
);

-- Control Library
CREATE TABLE controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id UUID REFERENCES frameworks(id),
    control_id VARCHAR(100) NOT NULL,  -- e.g., "PE-03", "AC-02"
    title VARCHAR(500) NOT NULL,
    description TEXT,
    control_family VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(framework_id, control_id)
);

-- Cross-Framework Mapping
CREATE TABLE control_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_control_id UUID REFERENCES controls(id),
    target_control_id UUID REFERENCES controls(id),
    mapping_type VARCHAR(50) NOT NULL,  -- 'direct', 'partial', 'conditional'
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    mapping_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    UNIQUE(source_control_id, target_control_id)
);

-- Evidence Artifacts
CREATE TABLE evidence_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(255),
    content_text TEXT,  -- Extracted text for RAG
    embedding_vector VECTOR(1024),  -- NVIDIA embedding dimension
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Evidence-to-Control Mapping
CREATE TABLE evidence_control_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES evidence_artifacts(id),
    control_id UUID REFERENCES controls(id),
    weightage DECIMAL(5,2) NOT NULL,  -- Percentage weightage
    mapping_status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected
    validation_notes TEXT,
    mapped_by UUID REFERENCES users(id),
    mapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_by UUID REFERENCES users(id),
    validated_at TIMESTAMP
);

-- Gap Analysis
CREATE TABLE gap_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id UUID REFERENCES controls(id),
    framework_id UUID REFERENCES frameworks(id),
    gap_description TEXT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    risk_score DECIMAL(5,2),
    remediation_plan TEXT,
    target_remediation_date DATE,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Review Workflow
CREATE TABLE review_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- evidence, mapping, gap_analysis
    entity_id UUID NOT NULL,
    workflow_status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected
    submitted_by UUID REFERENCES users(id),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    approval_level INTEGER DEFAULT 1
);

-- Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users and Roles
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,  -- admin, reviewer, analyst, viewer
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Agent Sessions and Memory
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_type VARCHAR(50) NOT NULL,  -- chat, analysis, review
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    context JSONB,
    memory_summary TEXT
);

-- Knowledge Base (for RAG)
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255),
    content_type VARCHAR(50),  -- policy, procedure, standard, guidance
    framework_id UUID REFERENCES frameworks(id),
    embedding_vector VECTOR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE
);
```

### 3.2 Indexes for Performance

```sql
-- Performance Indexes
CREATE INDEX idx_controls_framework ON controls(framework_id);
CREATE INDEX idx_controls_control_id ON controls(control_id);
CREATE INDEX idx_control_mappings_source ON control_mappings(source_control_id);
CREATE INDEX idx_control_mappings_target ON control_mappings(target_control_id);
CREATE INDEX idx_evidence_control_mappings_control ON evidence_control_mappings(control_id);
CREATE INDEX idx_evidence_control_mappings_evidence ON evidence_control_mappings(evidence_id);
CREATE INDEX idx_gap_analyses_control ON gap_analyses(control_id);
CREATE INDEX idx_gap_analyses_status ON gap_analyses(status);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_knowledge_base_framework ON knowledge_base(framework_id);

-- Vector Indexes for Similarity Search
CREATE INDEX idx_evidence_embedding ON evidence_artifacts USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
```

---

## 4. API Endpoints

### 4.1 Framework Management

```
GET    /api/v1/frameworks                    # List all frameworks
POST   /api/v1/frameworks                    # Create new framework
GET    /api/v1/frameworks/{id}               # Get framework details
PUT    /api/v1/frameworks/{id}               # Update framework
DELETE /api/v1/frameworks/{id}               # Delete framework (soft delete)

GET    /api/v1/frameworks/{id}/controls      # List controls for framework
POST   /api/v1/frameworks/{id}/controls      # Add control to framework
```

### 4.2 Control Mapping

```
GET    /api/v1/controls                      # List all controls
GET    /api/v1/controls/{id}                 # Get control details
GET    /api/v1/controls/{id}/mappings        # Get mappings for control

POST   /api/v1/control-mappings              # Create control mapping
GET    /api/v1/control-mappings              # List all mappings
PUT    /api/v1/control-mappings/{id}         # Update mapping
DELETE /api/v1/control-mappings/{id}         # Remove mapping

POST   /api/v1/control-mappings/auto-suggest # AI-powered mapping suggestions
```

### 4.3 Evidence Management

```
POST   /api/v1/evidence                      # Upload evidence artifact
GET    /api/v1/evidence                      # List evidence artifacts
GET    /api/v1/evidence/{id}                 # Get evidence details
PUT    /api/v1/evidence/{id}                 # Update evidence metadata
DELETE /api/v1/evidence/{id}                 # Delete evidence

POST   /api/v1/evidence/{id}/map-to-control  # Map evidence to control
GET    /api/v1/evidence/{id}/mappings        # Get evidence mappings
PUT    /api/v1/evidence/{id}/weightage       # Update evidence weightage
```

### 4.4 Gap Analysis

```
POST   /api/v1/gap-analyses                  # Create gap analysis
GET    /api/v1/gap-analyses                  # List gap analyses
GET    /api/v1/gap-analyses/{id}             # Get gap analysis details
PUT    /api/v1/gap-analyses/{id}             # Update gap analysis
POST   /api/v1/gap-analyses/auto-detect      # AI-powered gap detection

GET    /api/v1/reports/gap-summary           # Gap summary report
GET    /api/v1/reports/risk-heatmap          # Risk heatmap data
```

### 4.5 Review Workflow

```
POST   /api/v1/reviews                       # Submit for review
GET    /api/v1/reviews                       # List pending reviews
GET    /api/v1/reviews/{id}                  # Get review details
PUT    /api/v1/reviews/{id}/approve          # Approve submission
PUT    /api/v1/reviews/{id}/reject           # Reject submission
GET    /api/v1/reviews/my-pending            # Get user's pending reviews
```

### 4.6 Agent System

```
POST   /api/v1/agent/chat                    # Send message to GRC chatbot
GET    /api/v1/agent/sessions                # List agent sessions
GET    /api/v1/agent/sessions/{id}           # Get session details
POST   /api/v1/agent/analyze-evidence        # AI evidence analysis
POST   /api/v1/agent/suggest-mapping         # AI mapping suggestions
POST   /api/v1/agent/generate-report         # AI report generation
```

### 4.7 RAG System

```
POST   /api/v1/rag/search                    # Search knowledge base
POST   /api/v1/rag/ingest                    # Ingest documents
GET    /api/v1/rag/sources                   # List knowledge sources
POST   /api/v1/rag/sources                   # Add knowledge source
```

### 4.8 Audit and Reporting

```
GET    /api/v1/audit-logs                    # List audit logs
GET    /api/v1/audit-logs/{id}               # Get audit log details
GET    /api/v1/audit-logs/entity/{type}/{id} # Get logs for entity

GET    /api/v1/reports/compliance-status     # Compliance status report
GET    /api/v1/reports/framework-comparison  # Framework comparison
GET    /api/v1/reports/export/{format}       # Export reports (PDF, Excel)
```

### 4.9 System Configuration

```
GET    /api/v1/config/environment            # Get current environment
GET    /api/v1/config/features               # Get feature flags
PUT    /api/v1/config/features               # Update feature flags
GET    /api/v1/config/ai-models              # Get AI model configuration
```

---

## 5. Agent System Design

### 5.1 Agno Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agno Agent System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Agent Core      │    │   Memory System   │                   │
│  │   (Agno Runtime)  │◄──►│   (Session +      │                   │
│  │                   │    │    Long-term)      │                   │
│  └──────────────────┘    └──────────────────┘                   │
│           │                       │                              │
│           │                       │                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Knowledge Base  │    │   Guardrails     │                   │
│  │   (RAG System)    │    │   Manager        │                   │
│  │   - Compliance     │    │   - Input/Output │                   │
│  │   - Frameworks     │    │   - Compliance   │                   │
│  │   - Policies       │    │   - Security     │                   │
│  └──────────────────┘    └──────────────────┘                   │
│           │                       │                              │
│           │                       │                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Tool Registry   │    │   Human-in-      │                   │
│  │   - DB Operations │    │   the-Loop       │                   │
│  │   - File Parsing  │    │   Interface      │                   │
│  │   - API Calls     │    │   - Review Queue │                   │
│  │   - Calculations  │    │   - Approval     │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Agent Types and Responsibilities

**1. GRC Chatbot Agent**
- **Purpose**: Natural language interface for GRC queries
- **Capabilities**: Answer compliance questions, explain controls, guide users
- **Memory**: Conversation history, user preferences, previous queries
- **Guardrails**: No sensitive data exposure, compliance-accurate responses

**2. Evidence Analysis Agent**
- **Purpose**: Analyze uploaded evidence artifacts
- **Capabilities**: Extract text, identify control relevance, suggest mappings
- **Tools**: Document parser, OCR, embedding generation, similarity search
- **Guardrails**: Data validation, confidence scoring, human review triggers

**3. Mapping Suggestion Agent**
- **Purpose**: Suggest cross-framework control mappings
- **Capabilities**: Analyze control descriptions, identify overlaps, calculate confidence
- **Knowledge**: Framework-specific mappings, industry standards
- **Guardrails**: Mapping confidence thresholds, expert validation requirements

**4. Gap Analysis Agent**
- **Purpose**: Identify compliance gaps and assess risks
- **Capabilities**: Compare evidence against requirements, score risks
- **Tools**: Gap detection algorithms, risk scoring models
- **Guardrails**: Risk score validation, remediation plan requirements

**5. Report Generation Agent**
- **Purpose**: Generate compliance reports and summaries
- **Capabilities**: Create executive summaries, detailed analyses, visualizations
- **Tools**: Template engine, chart generation, PDF creation
- **Guardrails**: Data accuracy validation, branding compliance

### 5.3 Memory System Design

**Session Memory (Short-term)**
- Current conversation context
- Recent interactions and queries
- Temporary analysis results
- User session preferences

**Long-term Memory**
- User interaction history
- Previously approved mappings
- Validated evidence assessments
- learned preferences and patterns

**Knowledge Memory**
- Compliance framework knowledge
- Industry best practices
- Historical audit findings
- Organizational policies

### 5.4 Guardrails System

**Input Guardrails**
- PII detection and masking
- Malicious input detection
- Input validation and sanitization
- Rate limiting and abuse prevention

**Output Guardrails**
- Compliance accuracy validation
- Confidence scoring and thresholds
- Sensitive data exposure prevention
- Branding and formatting compliance

**Process Guardrails**
- Human-in-the-loop triggers
- Escalation procedures
- Audit trail requirements
- Rollback capabilities

---

## 6. Configuration Management Approach

### 6.1 Environment Configuration

```python
# config/environment.py
import os
from enum import Enum
from typing import Optional

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Config:
    def __init__(self):
        self.env = Environment(os.getenv("GRC_ENV", "development"))
        
    @property
    def is_development(self) -> bool:
        return self.env == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.env == Environment.PRODUCTION

class DatabaseConfig(Config):
    @property
    def connection_string(self) -> str:
        if self.is_development:
            return os.getenv("DEV_DATABASE_URL", 
                "postgresql://user:pass@localhost:5432/grc_dev")
        else:
            return os.getenv("PROD_DATABASE_URL",
                "postgresql://user:pass@db-server:5432/grc_prod")
    
    @property
    def pool_size(self) -> int:
        return 5 if self.is_development else 20

class LLMConfig(Config):
    @property
    def provider(self) -> str:
        return "openrouter" if self.is_development else "ollama"
    
    @property
    def model(self) -> str:
        if self.is_development:
            return "openrouter/meta-llama/llama-3-8b-instruct"
        else:
            return "ollama/gemma2:12b"
    
    @property
    def api_key(self) -> Optional[str]:
        if self.is_development:
            return os.getenv("OPENROUTER_API_KEY")
        else:
            return None  # Ollama doesn't need API key

class EmbeddingConfig(Config):
    @property
    def model(self) -> str:
        return "nvidia/llama-nemotron-embed-vl-1b-v2"
    
    @property
    def dimension(self) -> int:
        return 1024

class StorageConfig(Config):
    @property
    def upload_dir(self) -> str:
        if self.is_development:
            return "./uploads"
        else:
            return "/data/grc/uploads"
    
    @property
    def max_file_size(self) -> int:  # in MB
        return 50 if self.is_development else 500
```

### 6.2 Feature Flags

```python
# config/feature_flags.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FeatureFlags:
    # AI Features
    enable_ai_chat: bool = True
    enable_auto_mapping: bool = True
    enable_gap_analysis: bool = True
    enable_report_generation: bool = True
    
    # Guardrails
    enable_input_validation: bool = True
    enable_output_scoring: bool = True
    require_human_review: bool = True
    
    # Integration Features
    enable_audit_logging: bool = True
    enable_rag_system: bool = True
    enable_webhooks: bool = False
    
    # Development Features
    enable_mock_data: bool = False
    enable_debug_mode: bool = False

class FeatureFlagManager:
    def __init__(self, config: Dict[str, Any]):
        self.flags = FeatureFlags(**config)
    
    def is_enabled(self, feature: str) -> bool:
        return getattr(self.flags, feature, False)
    
    def update_flag(self, feature: str, enabled: bool) -> None:
        if hasattr(self.flags, feature):
            setattr(self.flags, feature, enabled)
```

### 6.3 Environment Variables

```bash
# .env.development
GRC_ENV=development
DEV_DATABASE_URL=postgresql://user:pass@localhost:5432/grc_dev
OPENROUTER_API_KEY=your_openrouter_key
ENABLE_MOCK_DATA=true
ENABLE_DEBUG_MODE=true
LOG_LEVEL=DEBUG

# .env.production
GRC_ENV=production
PROD_DATABASE_URL=postgresql://user:pass@db-server:5432/grc_prod
OLLAMA_BASE_URL=http://localhost:11434
ENABLE_MOCK_DATA=false
ENABLE_DEBUG_MODE=false
LOG_LEVEL=INFO
SECRET_KEY=your_production_secret_key
```

### 6.4 Configuration Files

```yaml
# config/settings.yaml
development:
  database:
    host: localhost
    port: 5432
    name: grc_dev
  llm:
    provider: openrouter
    model: meta-llama/llama-3-8b-instruct
    temperature: 0.7
  embedding:
    model: nvidia/llama-nemotron-embed-vl-1b-v2
    dimension: 1024
  storage:
    upload_dir: ./uploads
    max_file_size: 50MB

production:
  database:
    host: ${PROD_DB_HOST}
    port: 5432
    name: grc_prod
  llm:
    provider: ollama
    model: gemma2:12b
    temperature: 0.3
  embedding:
    model: nvidia/llama-nemotron-embed-vl-1b-v2
    dimension: 1024
  storage:
    upload_dir: /data/grc/uploads
    max_file_size: 500MB
  gpu:
    enabled: true
    device: mi300x
```

---

## 7. Deployment Strategy

### 7.1 Development Environment (Windows)

**Local Setup:**
```bash
# Windows Development Setup
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup PostgreSQL with pgvector
# Use Docker for PostgreSQL
docker run -d --name grc-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_DB=grc_dev \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 3. Install Ollama for local testing
# Download from https://ollama.ai

# 4. Run development server
export GRC_ENV=development
streamlit run app.py --server.port 8501
uvicorn api.main:app --reload --port 8000
```

**Development Scripts:**
```python
# scripts/dev_setup.py
import subprocess
import os

def setup_development():
    """Setup development environment"""
    # Install dependencies
    subprocess.run(["pip", "install", "-r", "requirements.txt"])
    
    # Start PostgreSQL container
    subprocess.run([
        "docker", "run", "-d", "--name", "grc-postgres",
        "-e", "POSTGRES_USER=user",
        "-e", "POSTGRES_PASSWORD=pass",
        "-e", "POSTGRES_DB=grc_dev",
        "-p", "5432:5432",
        "pgvector/pgvector:pg16"
    ])
    
    # Initialize database
    subprocess.run(["python", "scripts/init_db.py"])
    
    # Generate mock data
    subprocess.run(["python", "scripts/generate_mock_data.py"])
    
    print("Development environment ready!")

if __name__ == "__main__":
    setup_development()
```

### 7.2 Production Environment (Linux + MI300X GPU)

**Docker Configuration:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV GRC_ENV=production
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8000 8501

# Run application
CMD ["python", "scripts/start_production.py"]
```

**Docker Compose for Production:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: grc_prod
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  grc-api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    environment:
      - GRC_ENV=production
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/grc_prod
      - OLLAMA_BASE_URL=http://ollama:11434
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - ollama
    restart: unless-stopped

  grc-frontend:
    build: .
    command: streamlit run app.py --server.port 8501 --server.address 0.0.0.0
    environment:
      - GRC_ENV=production
      - API_URL=http://grc-api:8000
    ports:
      - "8501:8501"
    depends_on:
      - grc-api
    restart: unless-stopped

volumes:
  postgres_data:
  ollama_data:
```

### 7.3 Deployment Scripts

```python
# scripts/deploy_production.py
import subprocess
import os
from datetime import datetime

class ProductionDeployer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def pre_deployment_checks(self):
        """Run pre-deployment checks"""
        checks = [
            self.check_database_connection,
            self.check_gpu_availability,
            self.check_disk_space,
            self.check_memory_requirements
        ]
        
        for check in checks:
            if not check():
                raise Exception(f"Pre-deployment check failed: {check.__name__}")
    
    def check_database_connection(self) -> bool:
        """Verify database connectivity"""
        # Implementation to check PostgreSQL connection
        return True
    
    def check_gpu_availability(self) -> bool:
        """Verify MI300X GPU is available"""
        # Implementation to check GPU
        return True
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        # Implementation to check disk space
        return True
    
    def check_memory_requirements(self) -> bool:
        """Check memory requirements"""
        # Implementation to check memory
        return True
    
    def deploy(self):
        """Main deployment process"""
        print(f"Starting deployment at {self.timestamp}")
        
        # Pre-deployment checks
        self.pre_deployment_checks()
        
        # Build and deploy
        self.build_docker_images()
        self.deploy_database_migrations()
        self.deploy_application()
        self.verify_deployment()
        
        print(f"Deployment completed at {datetime.now()}")
    
    def build_docker_images(self):
        """Build Docker images"""
        subprocess.run([
            "docker-compose", "-f", "docker-compose.prod.yml",
            "build"
        ])
    
    def deploy_database_migrations(self):
        """Run database migrations"""
        subprocess.run([
            "docker-compose", "-f", "docker-compose.prod.yml",
            "exec", "grc-api", "python", "scripts/run_migrations.py"
        ])
    
    def deploy_application(self):
        """Deploy application"""
        subprocess.run([
            "docker-compose", "-f", "docker-compose.prod.yml",
            "up", "-d"
        ])
    
    def verify_deployment(self):
        """Verify deployment is successful"""
        # Health checks and verification
        subprocess.run([
            "docker-compose", "-f", "docker-compose.prod.yml",
            "ps"
        ])

if __name__ == "__main__":
    deployer = ProductionDeployer()
    deployer.deploy()
```

### 7.4 Monitoring and Logging

```python
# monitoring/health_check.py
import asyncio
import aiohttp
from datetime import datetime

class HealthChecker:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def check_api_health(self) -> bool:
        """Check API health endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                return response.status == 200
    
    async def check_database_health(self) -> bool:
        """Check database connectivity"""
        # Implementation to check database
        return True
    
    async def check_llm_health(self) -> bool:
        """Check LLM service health"""
        # Implementation to check Ollama/OpenRouter
        return True
    
    async def run_health_checks(self) -> dict:
        """Run all health checks"""
        checks = {
            "api": await self.check_api_health(),
            "database": await self.check_database_health(),
            "llm": await self.check_llm_health(),
            "timestamp": datetime.now().isoformat()
        }
        return checks
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Project structure setup
- [ ] Database schema implementation
- [ ] Basic API endpoints
- [ ] Streamlit frontend scaffolding
- [ ] Configuration management

### Phase 2: Core Features (Weeks 3-4)
- [ ] Framework/control management
- [ ] Evidence upload and mapping
- [ ] Basic gap analysis
- [ ] Audit logging

### Phase 3: AI Integration (Weeks 5-6)
- [ ] Agno agent setup
- [ ] RAG system implementation
- [ ] Guardrails system
- [ ] Human-in-the-loop workflow

### Phase 4: Advanced Features (Weeks 7-8)
- [ ] Cross-framework mapping
- [ ] Risk scoring algorithms
- [ ] Report generation
- [ ] Advanced analytics

### Phase 5: Deployment (Weeks 9-10)
- [ ] Production environment setup
- [ ] Docker configuration
- [ ] Deployment scripts
-   Monitoring and logging

---

## 9. Key Design Decisions

1. **Modular Architecture**: Clear separation between presentation, business logic, AI, and data layers
2. **Environment-Aware Configuration**: Dev/prod switching via environment flags
3. **Agent-Centric Design**: Agno library for AI capabilities with guardrails
4. **Vector-First Approach**: pgvector for RAG and similarity search
5. **Human-in-the-Loop**: Required for critical decisions and AI outputs
6. **Audit Everything**: Comprehensive logging for compliance requirements
7. **GPU Optimization**: MI300X support for production LLM inference
8. **Simple Dependencies**: Minimal external libraries for reliability

---

**End of Architecture Document**
