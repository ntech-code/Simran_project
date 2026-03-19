# 📊 Indian Tax Analysis System - UML Diagrams

This directory contains comprehensive PlantUML diagrams documenting the system architecture, classes, sequences, and component relationships.

## 📁 Diagram Files

| File | Description | Pages |
|------|-------------|-------|
| `class_diagram.puml` | Complete class diagram with all agents, models, and relationships | 1 |
| `sequence_diagram.puml` | Sequence diagrams for all major workflows | 7 |
| `architecture_diagram.puml` | System architecture with all layers and components | 1 |
| `component_diagram.puml` | Detailed component breakdown with internal methods | 1 |
| `data_flow_diagram.puml` | Data movement through the system | 1 |
| `deployment_diagram.puml` | Infrastructure and container deployment | 1 |
| `state_machine_diagram.puml` | Agent lifecycle state machines | 5 |

## 🔧 How to Render

### Option 1: PlantUML Online Server
1. Go to [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. Copy and paste the contents of any `.puml` file
3. Click "Submit" to render

### Option 2: VS Code Extension
1. Install "PlantUML" extension by jebbs
2. Open any `.puml` file
3. Press `Alt + D` to preview

### Option 3: Command Line (JAR)
```bash
# Install PlantUML
# Download from: https://plantuml.com/download

# Render to PNG
java -jar plantuml.jar class_diagram.puml

# Render to SVG
java -jar plantuml.jar -tsvg class_diagram.puml

# Render all diagrams
java -jar plantuml.jar *.puml
```

### Option 4: Docker
```bash
# Run PlantUML server locally
docker run -d -p 8080:8080 plantuml/plantuml-server:jetty

# Access at http://localhost:8080
```

## 📋 Diagram Details

### 1. Class Diagram (`class_diagram.puml`)

**Packages Covered:**
- `api` - FastAPI application and endpoints
- `models` - Pydantic request/response models
- `agents` - All 5 agent classes with methods
- `rules` - Tax rule domain entities
- `responses` - Data Transfer Objects
- `external` - External service interfaces
- `data_processing` - Utility classes

**Key Classes:**
- `TaxAnalyzerAgent` - Core computation with fraud detection
- `TaxChatbotAgent` - Conversational AI with memory
- `TaxRuleGeneratorAgent` - Static rule generation
- `DynamicTaxRuleGeneratorAgent` - Live crawling agent
- `TransactionAnalyzerAgent` - File processing agent

---

### 2. Sequence Diagrams (`sequence_diagram.puml`)

**Contains 7 Workflow Sequences:**

| Page | Workflow | Participants |
|------|----------|--------------|
| 1 | Tax Calculation Flow | User → Frontend → API → TaxAnalyzer → Rules |
| 2 | Regime Comparison Flow | User → Frontend → API → TaxAnalyzer → Both Rules |
| 3 | AI Chatbot Conversation | User → Chatbot → Gemini AI |
| 4 | Transaction File Analysis | User → Upload → Agent → Pandas → Gemini |
| 5 | Tax Rule Generation | Admin → API → RuleGen → Gov Sites → Gemini |
| 6 | Report Generation | User → Frontend → API → TaxAnalyzer |
| 7 | Google OAuth Authentication | User → Frontend → Google OAuth → LocalStorage |

---

### 3. Architecture Diagram (`architecture_diagram.puml`)

**Layers Documented:**
- **Presentation Layer** - React frontend with pages and components
- **Application Layer** - FastAPI with endpoints and middleware
- **Agent Layer** - Custom multi-agent framework
- **Data Layer** - JSON rules and temporary storage
- **External Services** - Gemini AI, Google OAuth, Government sites
- **Infrastructure Layer** - Docker, networking, environment

---

### 4. Component Diagram (`component_diagram.puml`)

**Package Breakdown:**
- Frontend: `pages/`, `components/`, `context/`, `utils/`
- Backend: `main.py` with all endpoints and models
- Agents: Each agent file with all methods listed
- Dependencies: All external libraries categorized

---

### 5. Data Flow Diagram (`data_flow_diagram.puml`)

**Processes Documented:**
- P1: User Authentication
- P2: Tax Data Input & Validation
- P3: Data Visualization
- P4: File Upload
- P5-P6: API Request Routing & Validation
- P7-P11: Agent Processing

**Data Stores:**
- D1: Browser LocalStorage
- D2: Tax Rules JSON Files
- D3: Agent Memory State
- D4: Temporary Files

---

### 6. Deployment Diagram (`deployment_diagram.puml`)

**Environments:**
- User Environment (Browser)
- Development Machine (Python + Node.js)
- Production Server (Docker containers)
- External Cloud Services (Google)

**Container Specifications:**
- Backend: python:3.11-slim on port 8000
- Frontend: nginx:alpine on port 80
- Network: tax-network (bridge)

---

### 7. State Machine Diagrams (`state_machine_diagram.puml`)

**Agent Lifecycles (5 pages):**

| Page | Agent | Key States |
|------|-------|------------|
| 1 | TaxAnalyzerAgent | Uninitialized → Initialized → RulesLoaded → Calculating/DetectingFraud |
| 2 | TaxChatbotAgent | Uninitialized → Initialized (NoContext/HasContext) → Processing → Streaming |
| 3 | TransactionAnalyzerAgent | Uninitialized → Ready → AnalyzingFile (Read/Clean/Summarize/AI) |
| 4 | TaxRuleGeneratorAgent | Uninitialized → Initialized → GeneratingRules (Validate/Fetch/Extract/Save) |
| 5 | DynamicTaxRuleGeneratorAgent | Uninitialized → Initialized → Crawling → LiveExtraction → GoogleSearchGrounding |

---

## 🎨 Theme Configuration

All diagrams use the `cerulean` theme with custom color coding:

| Color Code | Meaning |
|------------|---------|
| `#E8F5E9` | Frontend Layer (Green) |
| `#E3F2FD` | Backend/API Layer (Blue) |
| `#FCE4EC` | Agent Layer (Pink) |
| `#FFF3E0` | Data Layer (Orange) |
| `#F3E5F5` | External Services (Purple) |
| `#ECEFF1` | Infrastructure (Grey) |

---

## 📝 Notes

1. **Multi-page diagrams**: Sequence and State Machine diagrams use `newpage` for multiple pages
2. **Stereotypes**: Classes use `<<Agent>>`, `<<Pydantic>>`, `<<DTO>>` etc. for clarity
3. **Packages**: All diagrams use package grouping for organization
4. **Notes**: Key design decisions are documented inline with notes

---

## 🔗 References

- [PlantUML Official Documentation](https://plantuml.com/)
- [PlantUML Themes](https://plantuml.com/theme)
- [Class Diagram Syntax](https://plantuml.com/class-diagram)
- [Sequence Diagram Syntax](https://plantuml.com/sequence-diagram)
- [Component Diagram Syntax](https://plantuml.com/component-diagram)
- [State Diagram Syntax](https://plantuml.com/state-diagram)
- [Deployment Diagram Syntax](https://plantuml.com/deployment-diagram)

---

**Generated for: Indian Tax Analysis System v1.0.0**
**Author: Pratham Solanki**
**Date: January 2026**
