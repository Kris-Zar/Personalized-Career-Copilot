# 🚀 XCL PathFinder - Adaptive AI Career Copilot

> **AI-Powered Adaptive Learning-Path Recommender & Copilot with Evidence-Based Knowledge Assessment, Prerequisite-Aware Competency Modeling, Dynamic Recommendations, and Continuous Feedback Adaptation.**

Built strictly to the **XCL Hackathon Round 2 Prototype Architecture Specification**.

---

## 🌟 Core Differentiators & Highlights

1. **Evidence Hierarchy (Self-Report vs. Demonstrated Knowledge)**:
   - Does not treat self-reported skill ratings as ground truth.
   - Measures diagnostic test performance (weight 1.0x - 2.0x) vs. claimed proficiency (weight 0.2x).
   - Generates visual radar and grouped bar charts contrasting Claimed vs. Demonstrated competencies.

2. **Prerequisite-Aware Competency DAG Engine**:
   - Models career tracks (e.g. *Machine Learning Engineer*, *Full-Stack AI Developer*) as Directed Acyclic Graphs (DAGs).
   - Uses Kahn's topological sort to sequence milestones and detect **prerequisite bottlenecks** (e.g. scheduling Probability & Statistics before Machine Learning Foundations).

3. **Multi-Signal Resource & Project Recommender**:
   - Ranks curated courses, hands-on GitHub projects, interactive exercises, and videos against learner gaps, preferred formats, and weekly time constraints.

4. **Continuous Feedback Adaptation Loop**:
   - Chat and progress events (e.g. *"Probability is too hard and I only have 30 minutes today"*) trigger real-time re-planning.
   - Injects bite-sized interactive exercises, resizes sprint batches, increments to **Roadmap v2 / v3**, and explains exactly what changed and why.

5. **Grounded AI Tutor (Google Gemini + Deterministic Fallback)**:
   - Natural language assistant answering questions about milestones, math derivations, and roadmap rationale without hallucinating fake scores or non-existent URLs.

---

## ☁️ Streamlit Community Cloud Hosting Guide

This project is 100% compatible with **Streamlit Community Cloud** (and Hugging Face Spaces / Render).

### 1-Click Streamlit Cloud Deployment:
1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: XCL PathFinder Prototype"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
   - Click **"New app"**.
   - Select your repository, branch (`main`), and set **Main file path** to `app.py`.
   - Under **Advanced settings**, set Python version to `3.11` (or `3.10+`) and add any optional secrets:
     ```toml
     GEMINI_API_KEY = "your_gemini_api_key_here"
     ```
   - Click **Deploy!** 🚀

---

## 🛠️ Local Installation & Quickstart

### Prerequisites
- Python 3.10 or 3.11

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
```
*(Note: If `GEMINI_API_KEY` is not provided, the system automatically uses its built-in deterministic intelligent tutor engine).*

### 3. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run the Automated CLI Demo Runner
To verify the full 10-step hackathon demo flow directly in the terminal:
```bash
python scripts/demo_cli.py
```

### 5. Run the Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🏗️ Repository Structure

```
├── app.py                             # Main Streamlit Application Entrypoint
├── requirements.txt                   # Dependency specifications
├── .env.example                       # Environment template
├── assets/
│   └── style.css                      # Ultra-modern glassmorphic stylesheet
├── data/
│   ├── skills/                        # Curated skill DAG graphs (ml_engineer.json, fullstack_ai.json)
│   ├── assessment/                    # Diagnostic question bank with weights & explanations
│   ├── resources/                     # Curated courses, projects & exercises catalog
│   └── goals/                         # Goal definitions & target proficiency maps
├── core/
│   ├── schemas/                       # Pydantic data contracts (Profile, Graph, Roadmap, Feedback)
│   ├── services/
│   │   ├── graph_service.py           # DAG topological ordering & DOT graph generator
│   │   ├── assessment_service.py      # Question delivery & weighted scoring
│   │   ├── knowledge_service.py       # Knowledge state tracker & evidence hierarchy
│   │   ├── gap_analyzer.py            # Bottleneck detection & gap calculation
│   │   ├── recommender.py             # Multi-signal resource & project ranking
│   │   ├── roadmap_engine.py          # Prerequisite-aware path planning & versioning
│   │   ├── adaptation_engine.py       # Feedback handler & roadmap recalculation
│   │   └── llm_service.py             # Centralized LLM adapter (Gemini + fallback)
│   └── storage/
│       └── store.py                   # Centralized session state persistence
├── ui/
│   ├── components/                    # Header, Graphviz DAG, Plotly charts, Roadmap cards, Chat
│   └── views/                         # 6-step multi-view UI workflow
├── scripts/
│   └── demo_cli.py                    # Standalone 10-step automated demo runner
└── tests/                             # Unit & Integration test suite
```

---

## 🧪 Verification & Demo Walkthrough (Section 22)

1. **Step 1: Profile**: Inspect Alex Chen's profile with self-reported 85% Python and 80% Probability.
2. **Step 2: Goal Discovery**: Conversational intake extracts target role (Machine Learning Engineer, 6 months, 8h/week).
3. **Step 3: Assessment**: Complete diagnostic assessment or click *"⚡ Pre-fill Demo Answers"*.
4. **Step 4: Gap Results**: Notice the severe gap in Probability (0% demonstrated vs 80% claimed), flagged as a critical bottleneck.
5. **Step 5: Roadmap v1**: Inspect generated roadmap where Stage 1 prioritizes Probability & Statistics before downstream ML.
6. **Step 6: AI Tutor**: Ask *"Why did you recommend Probability before ML?"* to receive grounded explanation.
7. **Step 7: Feedback Adaptation**: Submit feedback *"Probability is too difficult and I only have 30 minutes today"*.
8. **Step 8: Roadmap v2**: Observe real-time adaptation into **Roadmap v2** with injected bite-sized interactive exercises and adjusted pacing!
