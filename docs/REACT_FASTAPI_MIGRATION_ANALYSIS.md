# XCL PathFinder — React + FastAPI Migration Analysis

**Document Version:** 1.0.0  
**Date:** August 30, 2026  
**Objective:** Complete architecture and migration strategy to replace the Streamlit UI with a React (Vite + TypeScript) frontend powered by a high-performance FastAPI backend.

---

## 1. Repository Inventory & Component Classification

### 1.1 Python Core Intelligence (100% Reusable)
The intelligence layer contains the domain logic, topological graph algorithms, multi-signal recommendation scoring, knowledge calibration, and Gemini LLM integrations. **These files will NOT be rewritten or simplified.**

| Service File | Domain Responsibility | FastAPI Endpoint Consumers |
|---|---|---|
| [`core/services/llm_service.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/llm_service.py) | Gemini 3.6 Flash adapter, `LLMResult` result tracking, structured JSON extraction, grounded tutoring | `POST /api/goal/extract`, `POST /api/tutor/chat` |
| [`core/services/graph_service.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/graph_service.py) | Competency DAG loading, topological ordering, transitive prerequisite resolution | `GET /api/skill-graph/{goal_id}` |
| [`core/services/assessment_service.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/assessment_service.py) | Diagnostic assessment bank loader, difficulty & evidence weighting, item lookup | `GET /api/assessment`, `POST /api/assessment/attempt` |
| [`core/services/knowledge_service.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/knowledge_service.py) | Evidence-based knowledge state computation (scoring raw attempts against claimed baseline) | `POST /api/assessment/complete`, `GET /api/knowledge` |
| [`core/services/gap_analyzer.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/gap_analyzer.py) | Gap calculation, claimed vs demonstrated deficit identification, bottleneck detection | `GET /api/gaps` |
| [`core/services/recommender.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/recommender.py) | Multi-signal learning resource ranking & catalog curation | `GET /api/recommendations` |
| [`core/services/roadmap_engine.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/roadmap_engine.py) | Topological sequencing, milestone generation, time budgeting, Roadmap V1 | `GET /api/roadmap`, `POST /api/roadmap/generate` |
| [`core/services/adaptation_engine.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/services/adaptation_engine.py) | Feedback intent processing (10 intent types), dynamic DAG restructuring, Roadmap V2 | `POST /api/feedback`, `POST /api/roadmap/adapt` |

### 1.2 Pydantic Schemas (100% Reusable for FastAPI)
- [`core/schemas/profile.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/schemas/profile.py): `LearnerProfile`
- [`core/schemas/feedback.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/schemas/feedback.py): `GoalState`, `FeedbackEvent`, `AdaptationDiff`
- [`core/schemas/assessment.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/schemas/assessment.py): `AssessmentItem`, `AssessmentAttempt`, `KnowledgeState`, `GapReport`, `SkillGapItem`
- [`core/schemas/roadmap.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/schemas/roadmap.py): `Roadmap`, `RoadmapStage`, `Milestone`
- [`core/schemas/resource.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/schemas/resource.py): `LearningResource`
- [`core/schemas/skill_graph.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/schemas/skill_graph.py): `SkillGraph`, `SkillNode`

### 1.3 State Management
- [`core/storage/store.py`](file:///c:/Study%20content/Project/Personalized%20Career%20Copilot/core/storage/store.py): `InMemoryStore` provides the centralized, authoritative state container for profile, goals, attempts, knowledge states, roadmaps, and chat history.
- The FastAPI backend will inject a singleton `InMemoryStore` instance per session, backed by clean repository interfaces ready for database persistence.

### 1.4 Deprecated Streamlit Artifacts (To be archived into `legacy/streamlit/`)
- `app.py`
- `ui/views/*.py` (`view_profile.py`, `view_goal_discovery.py`, `view_assessment.py`, `view_results_gaps.py`, `view_roadmap.py`, `view_dashboard.py`)
- `ui/components/*.py` (`header.py`, `roadmap_view.py`, `chat_drawer.py`, `radar_chart.py`, `skill_graph_viz.py`)

---

## 2. Target React + FastAPI Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│               REACT + VITE + TYPESCRIPT FRONTEND (Port 5173)           │
│                                                                        │
│   TopNavigation · ThemeToggle (Light/Dark) · Signature MomentumMeter   │
│                                                                        │
│   ┌───────────┬─────────────┬────────────┬─────────┬─────────┬─────────┐ │
│   │ 01 Profile│ 02 Goal Disc│ 03 Assess  │04 Result│05 Rdmap │06 Dash  │ │
│   └───────────┴─────────────┴────────────┴─────────┴─────────┴─────────┘ │
│                                  │                                     │
│                     Centralized API Client (Axios / Fetch)             │
└──────────────────────────────────┼─────────────────────────────────────┘
                                   │ HTTP REST (JSON)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (Port 8000)                       │
│                                                                        │
│   /api/profile  ·  /api/goal  ·  /api/assessment  ·  /api/roadmap      │
│   /api/gaps     ·  /api/tutor ·  /api/feedback    ·  /api/dashboard    │
│                                  │                                     │
│                     FastAPI Dependency Injection                       │
│                                  │                                     │
│                  ┌───────────────┴───────────────┐                     │
│                  ▼                               ▼                     │
│         Authoritative State             Existing Python Services       │
│           (InMemoryStore)                 (Graph, Know, Gap, LLM,      │
│                                            Roadmap, Adaptation)        │
└──────────────────────────────────────────────────┬─────────────────────┘
                                                   │
                                                   ▼
                                          Gemini 3.6 Flash API
```

---

## 3. Migration Roadmap

1. **FastAPI Backend (`backend/`)**:
   - Initialize FastAPI app with CORS middleware (allowing `http://localhost:5173`).
   - Create modular REST API routers matching the full pipeline.
   - Add automated endpoint tests using `fastapi.testclient.TestClient`.
2. **React Frontend (`frontend/`)**:
   - Initialize Vite + React + TypeScript application.
   - Port all CSS styling, typography, cards, and theme switching from `PathFinder_Visual_Reference.html`.
   - Build strongly typed API client in `frontend/src/api/client.ts`.
   - Implement the 6 screen pages and reusable UI components.
3. **E2E Validation & QA**:
   - Run backend test suite.
   - Run live browser validation across the full lifecycle (Profile ➔ Goal ➔ Assessment ➔ Results ➔ Roadmap ➔ AI Tutor ➔ Feedback ➔ Adaptation ➔ Dashboard).
   - Capture 8 screenshots to `docs/react_ui_qa/`.
   - Document complete local execution instructions in `README.md`.
