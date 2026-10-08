# XCL PathFinder — REST API Specification

**Specification Version:** 2.0.0  
**Base URL:** `http://localhost:8000/api`  
**OpenAPI Documentation:** `http://localhost:8000/docs` / `http://localhost:8000/redoc`

---

## 1. System Health & Metadata

### `GET /api/health`
Checks API server health, active Gemini AI configuration, and authoritative store status.

- **Request Body:** None
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "service": "XCL PathFinder FastAPI Backend",
  "version": "2.0.0",
  "gemini_model": "gemini-3.6-flash",
  "gemini_configured": true,
  "authoritative_store": {
    "profile_loaded": true,
    "goal_active": true,
    "knowledge_states_count": 10,
    "active_roadmap_version": 1,
    "feedback_events_count": 0
  }
}
```

---

## 2. Learner Profile Baseline

### `GET /api/profile`
Retrieves the active learner profile baseline.

- **Response `200 OK`:** `LearnerProfile`

### `PUT /api/profile`
Updates self-reported profile baseline, weekly study hours, timeline, and skill ratings.

- **Request Body:**
```json
{
  "name": "Alex Chen",
  "email": "alex.chen@example.com",
  "current_role": "Biology Student",
  "interests": ["Machine Learning", "Bioinformatics"],
  "self_reported_skills": {
    "py_core": 0.85,
    "math_prob_stats": 0.80,
    "ml_foundations": 0.50
  },
  "previous_learning": ["Python Bootcamp"],
  "weekly_hours": 8.0,
  "timeline_months": 6,
  "content_preferences": ["projects", "interactive", "videos"]
}
```
- **Response `200 OK`:** `LearnerProfile`

---

## 3. Conversational Goal Discovery

### `GET /api/goal`
Retrieves currently active career goal checkpoint.

### `GET /api/goal/catalog`
Retrieves all curated career track templates in the catalog (`Data Scientist`, `Machine Learning Engineer`, `Full-Stack AI Developer`).

### `POST /api/goal/extract`
Extracts structured parameters from natural language goal statements using **Gemini 3.6 Flash**.

- **Request Body:**
```json
{
  "user_prompt": "I want to become an industry-ready Data Scientist within 6 months. I have about 8 hours per week to study."
}
```
- **Response `200 OK`:**
```json
{
  "extracted": {
    "target_role": "Data Scientist",
    "timeline_months": 6,
    "weekly_hours": 8.0,
    "interests": ["Machine Learning", "Data Analysis"]
  },
  "goal_state": {
    "goal_id": "goal_data_scientist",
    "target_role": "Data Scientist",
    "timeline_months": 6,
    "weekly_hours": 8.0,
    "active": true
  },
  "source": "gemini",
  "model": "gemini-3.6-flash",
  "error": null
}
```

### `POST /api/goal/select`
Manually selects a track template from catalog.

---

## 4. Competency Graph & Assessment

### `GET /api/skill-graph/{goal_id}`
Retrieves the competency DAG nodes, edges, and dependencies for the specified goal.

### `GET /api/assessment`
Retrieves all diagnostic assessment items with multiple-choice options, difficulty level, and mapped skills.

### `POST /api/assessment/attempt`
Records a single item attempt in the session.

### `POST /api/assessment/complete`
Scores all attempts, computes evidence-based `KnowledgeState` scores, calculates prerequisite deficits with `GapAnalyzer`, and generates `Roadmap V1`.

- **Request Body (Optional):**
```json
{
  "attempts": [
    { "item_id": "q_py_core_01", "answer": "def" },
    { "item_id": "q_prob_stats_01", "answer": "P(A|B) = P(B|A)*P(A)/P(B)" }
  ]
}
```
- **Response `200 OK`:**
```json
{
  "status": "success",
  "scored_attempts_count": 5,
  "knowledge_states": [...],
  "gap_report": { ... },
  "roadmap_v1": { ... }
}
```

---

## 5. Knowledge & Gaps

### `GET /api/knowledge`
Returns list of calibrated `KnowledgeState` objects (`adequate`, `needs_improvement`, `weak`).

### `GET /api/gaps`
Returns complete `GapReport` containing `comparison_data`, `unresolved_prerequisites`, and `weak_skills`.

### `GET /api/recommendations`
Returns multi-signal ranked `Recommendation` resources matching learner deficits and preferences.

---

## 6. Adaptive Roadmap

### `GET /api/roadmap`
Retrieves active or specified version of the roadmap (`?version=1` or `?version=2`).

### `GET /api/roadmap/versions`
Retrieves map of all generated roadmap versions.

### `POST /api/roadmap/generate`
Generates a new roadmap version from active store state.

---

## 7. AI Tutor & Continuous Adaptation

### `POST /api/tutor/chat`
Processes conversational queries with grounded Gemini AI or detects difficulty feedback to trigger dynamic adaptation.

- **Request Body:**
```json
{
  "query": "Probability is too difficult and I only have 30 minutes daily."
}
```
- **Response `200 OK` (Adaptation Trigger):**
```json
{
  "reply": "Understood, Alex Chen! I have recorded your feedback and updated your learner model.\n\n🔄 **Roadmap Adapted to Version 2:**\nIdentified difficulty bottleneck in 'Probability & Statistics'. Injected bite-sized visual exercises and slowed stage progression.\n\nI've injected bite-sized interactive exercises and adjusted pacing. Check out your updated Roadmap!",
  "source": "adaptation_engine",
  "model": "adaptation-engine-v2",
  "is_adaptation": true,
  "adaptation_diff": {
    "version_from": "v1",
    "version_to": "v2",
    "trigger_message": "Probability is too difficult and I only have 30 minutes daily.",
    "explanation": "Identified difficulty bottleneck in 'Probability & Statistics'. Injected bite-sized visual exercises and slowed stage progression."
  }
}
```

### `POST /api/feedback`
Explicitly logs a `FeedbackEvent` and triggers `AdaptationEngine`.

---

## 8. Master Dashboard & Presets

### `GET /api/dashboard`
Aggregated telemetry payload for the master cockpit.

### `POST /api/presets/load/{preset_id}`
Loads demo personas (`alex`, `kenji`, `aisha`) for 1-click test verification.

### `POST /api/presets/reset`
Resets authoritative store to clean blank state.
