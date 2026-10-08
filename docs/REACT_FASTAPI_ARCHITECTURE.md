# XCL PathFinder — React + FastAPI System Architecture

**Document Version:** 2.0.0  
**Date:** August 30, 2026  
**Stack:** React 18 + Vite + TypeScript (Frontend) | FastAPI + Uvicorn + Pydantic (Backend) | Gemini 3.6 Flash (LLM)

---

## 1. System Overview

XCL PathFinder has transitioned to a client-server architecture:
1. **Frontend (`frontend/`)**: React 18 single-page application built with Vite and TypeScript. Renders the design specification from `PathFinder_Visual_Reference.html` with theme switching, responsive layouts, interactive progress tracks, and real-time AI chat.
2. **Backend (`backend/`)**: FastAPI application exposing clean REST endpoints (`/api/*`). Handles state orchestration, validation, and delegates domain logic to Python intelligence services.
3. **Core Intelligence (`core/`)**: Untouched, battle-tested Python services managing DAG topological traversal, multi-signal recommendation scoring, knowledge state evidence calibration, and adaptation diffing.
4. **LLM Integration (`gemini-3.6-flash`)**: Grounded AI for goal extraction and tutoring queries with fallback protection.

---

## 2. Directory Structure

```
Personalized Career Copilot/
├── backend/                        # FastAPI Application
│   ├── api/                        # REST Routers
│   │   ├── assessment.py           # Diagnostic questions & scoring
│   │   ├── dashboard.py            # Cockpit telemetry
│   │   ├── feedback.py             # Feedback events & adaptation
│   │   ├── gaps.py                 # Skill gap analysis
│   │   ├── goal.py                 # Goal discovery & catalog
│   │   ├── graph.py                # Competency DAG
│   │   ├── knowledge.py            # Calibrated evidence states
│   │   ├── presets.py              # 1-Click demo personas
│   │   ├── profile.py              # Baseline profile management
│   │   ├── recommendations.py      # Curated learning resources
│   │   ├── roadmap.py              # Versioned learning roadmap
│   │   └── tutor.py                # Grounded Gemini AI chat
│   ├── dependencies.py             # Service Container & Dependency Injection
│   ├── main.py                     # App entrypoint, CORS, Health
│   └── schemas.py                  # API Request / Response schemas
├── core/                           # Domain Intelligence Layer
│   ├── schemas/                    # Pydantic domain models
│   ├── services/                   # Business logic engines
│   └── storage/                    # InMemoryStore state repository
├── data/                           # Catalogs & Assessment Bank
│   ├── assessment/
│   ├── goals/
│   ├── resources/
│   └── skills/
├── frontend/                       # React + Vite + TypeScript
│   ├── src/
│   │   ├── api/                    # Centralized API client (client.ts)
│   │   ├── components/             # Reusable UI components
│   │   ├── pages/                  # 6 Route screens
│   │   ├── styles/                 # Theme tokens & CSS
│   │   ├── types/                  # TypeScript interfaces
│   │   ├── App.tsx                 # Router & Layout
│   │   └── main.tsx                # React Root
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── legacy/                         # Deprecated Streamlit UI
│   └── streamlit/
└── tests/                          # Automated Unit & API Tests
```

---

## 3. End-to-End State Lifecycle

```
[React Frontend] (Port 5173)
       │
       │  1. PUT /api/profile (Name, Background, Hours, Baseline)
       ▼
[FastAPI] ──> [InMemoryStore.profile]
       │
       │  2. POST /api/goal/extract ("Become Data Scientist in 6 months")
       ▼
[FastAPI] ──> [LLMService (Gemini 3.6 Flash)] ──> [InMemoryStore.goal_state]
       │
       │  3. GET /api/assessment ──> Render Diagnostic Questions
       │  4. POST /api/assessment/complete (Submit raw answers)
       ▼
[FastAPI] ──> [KnowledgeStateEngine] ──> [GapAnalyzer] ──> [RoadmapEngine]
       │             │                         │                  │
       │             ▼                         ▼                  ▼
       │      [knowledge_states]         [gap_report]        [Roadmap V1]
       │             └─────────────────────────┼──────────────────┘
       │                                       ▼
       │                                [InMemoryStore]
       │
       │  5. GET /api/dashboard ──> Render Cockpit, Progress, Badges, Metrics
       │
       │  6. POST /api/tutor/chat ("Probability is too difficult (30m/day)")
       ▼
[FastAPI] ──> [AdaptationEngine] ──> [Roadmap V2 generated with Diff]
       │
       ▼
[React Frontend] (Live update to Roadmap V2 with adaptation diff banner)
```

---

## 4. Local Startup Instructions

### Terminal 1: FastAPI Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
- API Health: `http://localhost:8000/api/health`
- Swagger Docs: `http://localhost:8000/docs`

### Terminal 2: React Frontend
```bash
cd frontend
npm install
npm run dev
```
- Application: `http://localhost:5173`
