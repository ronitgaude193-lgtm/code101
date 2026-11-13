# AI Coding Mentor – Intelligent Adaptive Programming Learning Platform

AI Coding Mentor is an end-to-end educational platform designed to teach students **how to think like programmers**, rather than simply giving away code. It combines an interactive Monaco-powered playground, safe isolated code execution, step-by-step visual Python execution tracing, forensic AI code autopsies, rule-based adaptive learning intelligence, and measurable Programming DNA profiling.

---

## 1. System Architecture & Folder Structure

```
d:\DBCE/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point, CORS, SPA static mount & health
│   │   ├── core/
│   │   │   ├── config.py            # Environment configuration (Pydantic)
│   │   │   └── security.py          # PBKDF2 password hashing & JWT token handling
│   │   ├── database/
│   │   │   ├── session.py           # Supabase PostgreSQL connection pool (psycopg)
│   │   │   └── schema.sql           # Schema (11 entities), indexes, RLS & seed data – run on startup
│   │   ├── schemas/
│   │   │   └── all_schemas.py       # Pydantic schemas for Auth, Submissions, Tracing, DNA, etc.
│   │   ├── auth/
│   │   │   └── router.py            # Registration, login, profile management
│   │   ├── challenges/
│   │   │   └── router.py            # Challenge explorer & AI Challenge Generator
│   │   ├── execution/
│   │   │   ├── service.py           # Unified execution service interface
│   │   │   ├── judge0_client.py     # Judge0 REST API client
│   │   │   ├── isolated_sandbox.py  # AST-validated isolated subprocess sandbox
│   │   │   ├── tracer_worker.py     # Isolated execution tracing worker (sys.settrace)
│   │   │   ├── visual_tracer.py     # Process spawner and timeout controller
│   │   │   └── router.py            # Run, Submit, and Trace endpoints
│   │   ├── ai_mentor/
│   │   │   ├── service.py           # Dual LLM (Gemini/OpenAI/Groq) & Offline Pedagogical Engine
│   │   │   └── router.py            # Learning, Debugging, Hint & Autopsy endpoints
│   │   ├── adaptive_learning/
│   │   │   └── engine.py            # Mastery score engine, weakness identification & DNA profiling
│   │   ├── analytics/
│   │   │   └── router.py            # Dashboard metrics & Programming DNA
│   │   └── achievements/
│   │       └── router.py            # Gamification milestones & badges
│   ├── tests/
│   │   ├── test_backend.py          # Unit & engine automated test suite
│   │   └── test_api_integration.py  # End-to-end REST API integration test suite
│   ├── requirements.txt             # Backend dependencies
│   └── .env.example                 # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts            # Typed HTTP client with automatic JWT injection
│   │   ├── context/
│   │   │   └── AuthContext.tsx      # Student session management & persistence
│   │   ├── types/
│   │   │   └── index.ts             # Complete TypeScript data models
│   │   ├── components/
│   │   │   ├── Navbar.tsx           # Global navigation, XP level, and streak badge
│   │   │   ├── MonacoPlayground.tsx # Monaco editor, language selector, stdin drawer, console
│   │   │   ├── VisualDebugger.tsx   # Step-by-step visual execution timeline & variables inspector
│   │   │   ├── AICodingMentor.tsx   # 3-mode pedagogical mentor (Learning, Debugging, Hints)
│   │   │   ├── AICodeAutopsy.tsx    # Forensic autopsy with loop timeline & misconception classification
│   │   │   ├── DNAProfileView.tsx   # Programming DNA metrics & archetype badges
│   │   │   ├── ChallengeSidebar.tsx # Challenge descriptions, constraints & test cases
│   │   │   └── AuthModal.tsx        # Registration and sign-in modal
│   │   ├── pages/
│   │   │   ├── PlaygroundPage.tsx   # Central 3-panel educational coding experience
│   │   │   ├── ChallengesPage.tsx   # Challenge repository & AI Challenge Generator
│   │   │   ├── DashboardPage.tsx    # Analytics dashboard, mastery levels & weaknesses
│   │   │   └── AchievementsPage.tsx # Gamification badges & milestones
│   │   ├── App.tsx                  # Root application router
│   │   └── App.css                  # Modern dark-mode educational technology theme
│   ├── dist/                        # Production build artifacts
│   ├── package.json                 # Frontend dependencies (React, Monaco, Lucide, Confetti)
│   └── vite.config.ts               # Vite configuration
├── run_app.py                       # Single-command unified application runner
└── README.md                        # Project documentation
```

---

## 2. Database Schema (11 Entities)

1. `users` – User registration, password hashes, full name, role (`student`).
2. `student_profiles` – XP, level, daily streak, preferred language, bio.
3. `coding_challenges` – Title, topic, difficulty, test cases (JSON), hints, XP reward.
4. `code_submissions` – Code submitted, language, status, execution duration, error type.
5. `execution_results` – Stdout, stderr, compile output, exit codes.
6. `ai_feedback` – Pedagogical mentor feedback, modes, hints revealed, misconceptions.
7. `learning_assessments` – Topic-wise calculated scores and recommendations.
8. `student_skills` – Topic mastery percentage (0-100%), problems solved/attempted, error count.
9. `learning_history` – Submission logs, XP earned, streak gained.
10. `achievements` – Milestone thresholds, badge icons, XP rewards.
11. `student_achievements` – Unlocked badges and timestamps.

---

## 3. Implementation Status Summary

| Module | Feature | Status | Notes |
|---|---|---|---|
| **MODULE A** | User Authentication & JWT | **IMPLEMENTED AND TESTED** | Secure PBKDF2 hashing, JWT HS256 tokens, protected routes. |
| **MODULE B** | Student Dashboard | **IMPLEMENTED AND TESTED** | Real data from DB: streaks, XP, level, solve rate, weaknesses. |
| **MODULE C** | Monaco Playground | **IMPLEMENTED AND TESTED** | Monaco Editor integrated with Python syntax, stdin drawer, console. |
| **MODULE D** | Code Execution Sandbox | **IMPLEMENTED AND TESTED** | Unified service: delegates to Judge0 if configured; isolated AST sandbox fallback. |
| **MODULE E** | AI Coding Mentor | **IMPLEMENTED AND TESTED** | 3 modes: Learning, Debugging, Progressive Hints. Multi-provider + Offline Engine. |
| **MODULE F** | AI Code Autopsy | **IMPLEMENTED AND TESTED** | Dissects root cause (e.g. index vs value), loop timeline, guiding hint. |
| **MODULE G** | Visual Code Execution Engine | **IMPLEMENTED AND TESTED** | `sys.settrace` adapter in isolated subprocess with timeline, play/pause & inspector. |
| **MODULE H** | Adaptive Learning Engine | **IMPLEMENTED AND TESTED** | Transparent rule-based skill mastery scoring & weakness recommendations. |
| **MODULE I** | AI Challenge Generator | **IMPLEMENTED AND TESTED** | Generates verified practice problems tailored to topic & difficulty. |
| **MODULE J** | Programming DNA Profile | **IMPLEMENTED AND TESTED** | 6 measurable skill dimensions & verifiable archetype classifications. |
| **MODULE K** | Learning Analytics | **IMPLEMENTED AND TESTED** | Skill progress bars, weakness heatmap, and activity history. |
| **MODULE L** | Gamification | **IMPLEMENTED AND TESTED** | XP leveling, streak tracking, achievements grid & celebratory confetti. |
| **Judge0 API** | External Hosted Judge0 | **BLOCKED BY MISSING CREDENTIALS** | Client ready in `judge0_client.py`. Uses safe isolated sandbox until key provided. |
| **LLM APIs** | Gemini / OpenAI / Groq | **BLOCKED BY MISSING CREDENTIALS** | Client ready in `service.py`. Uses high-accuracy offline pedagogical engine. |

---

## 4. Execution & Quick Start Instructions

### Running the Complete Application (Single Command):

1. Launch the unified application runner:
```powershell
.\.venv\Scripts\python.exe run_app.py
```
2. Open your web browser at:
   - **Application UI:** `http://127.0.0.1:8000`
   - **Interactive API Documentation:** `http://127.0.0.1:8000/docs`

### Development Mode (with Hot Module Replacement):

If editing frontend code with instant reload:
```powershell
# Terminal 1: Backend
$env:PYTHONPATH="d:\DBCE\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## 5. Automated Test Results

Two automated test suites were built and executed:

1. **Unit & Engine Test Suite (`backend/tests/test_backend.py`)**:
   - `[TEST 1/8]` Database Initialization & Relational Integrity -> **PASSED**
   - `[TEST 2/8]` PBKDF2 Password Hashing & JWT Signature Validation -> **PASSED**
   - `[TEST 3/8]` Isolated Code Execution & AST Security Filter -> **PASSED**
   - `[TEST 4/8]` Visual Execution Tracing (`sys.settrace` adapter) -> **PASSED**
   - `[TEST 5/8]` Challenge Submission Evaluation & Adaptive Skill Updating -> **PASSED**
   - `[TEST 6/8]` AI Mentor Pedagogical Guidance -> **PASSED**
   - `[TEST 7/8]` AI Code Autopsy & Loop Iteration Dissection -> **PASSED**
   - `[TEST 8/8]` Student Dashboard & Programming DNA Archetype Scoring -> **PASSED**

2. **REST API Full Integration Test Suite (`backend/tests/test_api_integration.py`)**:
   - Tested 10 live HTTP endpoints with authentic payloads -> **100% SUCCESS (10/10 Passed)**.

3. **Frontend Production Build**:
   - Built with Vite & TypeScript (`tsc -b && vite build`) -> **Zero Errors, compiled in 1.07s**.

---

## 6. External Service Configuration (`backend/.env`)

The backend stores all data in Supabase PostgreSQL. Create a `backend/.env` file (copy `backend/.env.example`) — `DATABASE_URL` is required; tables and seed data are created automatically on first startup from `backend/app/database/schema.sql`:

```env
# Database (REQUIRED) – Supabase PostgreSQL connection string (Dashboard -> Connect)
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Judge0 Execution Engine (Optional; isolated local sandbox is active by default)
JUDGE0_API_URL=
JUDGE0_API_KEY=

# AI Provider Integration (Optional; offline pedagogical rule engine is active by default)
AI_PROVIDER=gemini
AI_API_KEY=
AI_MODEL=gemini-1.5-flash
```

---

## 7. Security Architecture

1. **Untrusted Code Execution Isolation:**
   - Student code is **never** executed inside the main FastAPI application process.
   - Code is routed to Judge0 when configured.
   - In fallback mode, an isolated child process runs with a 4.0-second hard timeout and AST verification that blocks unauthorized imports (`os`, `subprocess`, `socket`, `shutil`, `ctypes`) and filesystem modifications.
2. **Visual Tracing Safety:**
   - Visual tracing runs in a separate child process capped at 150 steps and 3.5 seconds to prevent runaway while-loops.
3. **Authentication & Secret Integrity:**
   - Passwords salted and hashed with PBKDF2-SHA256 (100,000 iterations).
   - JWT tokens signed with HS256.
   - Credentials and database keys are never exposed to the frontend.
4. **SQL exercise sandbox:** student SQL runs in a separate process against a throwaway in-memory SQLite copy of the exercise dataset (4 s timeout, `ATTACH`/`DETACH`/`PRAGMA` blocked, runaway queries aborted). It never touches the Supabase database.

---

## 8. Learning Extensions

| Feature | Where | How it works |
|---|---|---|
| **Coding Academy** (C Programming, DBMS & SQL) | Academy tab · `backend/app/academy/` | 2 courses × 5 levels; each level has 3 lessons with a practice task and a level assessment (level 5 = final). C is compiled and tested by Judge0, SQL is checked against a reference query, quizzes against an answer key. Level *n* unlocks when level *n−1*'s assessment is passed. Content lives in `academy/content.py` and is seeded on startup; add a course by appending to `COURSES`. |
| **XP & badges** | existing XP system | Lessons, tasks, assessments and course completion award XP **once**, enforced by `UNIQUE (user_id, item_type, item_id)` on `course_completions`. Completing a course awards its badge in the existing Achievements table, shown with the course name and date. Challenges also award full XP only for the first accepted solution. |
| **30-Day Roadmap** | Roadmap tab · `backend/app/roadmap/` | Built deterministically from course progress, Mistake Memory, assessment weaknesses (`learning_assessments`), weak skills and current learning strain. Gemma only writes the focus summary and daily tips. A day completes only when its linked task is verified, and its XP is awarded once. |
| **Mistake Memory + Déjà Vu** | Memory tab, after failed submits · `backend/app/mistake_memory/` | Each failure is classified into a signature (Python uses the existing autopsy rule engine; C uses compiler/runtime evidence; SQL uses error and result comparison). Same signature = **repeat**, same concept = **related**, otherwise first time. Passing later stores your own fix. |
| **Memory Replay** | "Replay" buttons | Generic feedback (current code only, existing AI Mentor) next to personalised feedback (current code + at most 3 relevant past mistakes). Shows a first-time state when there is no relevant history. |
| **Learning-strain assistance** | after failed submits · `backend/app/assistance/` | Transparent rule-based score from consecutive failures, repeated mistakes, hint requests, declining accuracy, session length and lack of progress (real timestamps in `practice_attempts`). Offers a hint at ≥45 or after 3 failures, pauses after "No thanks", gives 3 progressive hints (conceptual → directional → guided, never the solution) and then recovery suggestions. Not a medical or psychological assessment. Hints are disabled during assessments. |
| **Light / Dark mode** | sun/moon button in the navbar | CSS tokens in `App.css` (`:root` and `:root[data-theme="light"]`), saved in `localStorage`, applied before first paint; Monaco follows the theme. All text tokens meet WCAG AA in both themes. |

New tables (all additive, created by `schema.sql`): `courses`, `course_levels`, `course_lessons`, `course_tasks`, `course_completions`, `practice_attempts`, `mistake_patterns`, `mistake_occurrences`, `hint_history`, `assistance_prompts`, `learning_roadmaps`, `roadmap_days`, plus `app_meta` for the content fingerprint.

**Tests**
- `backend/tests/validate_academy_content.py` checks that every C reference solution passes on Judge0, every SQL reference matches, every quiz key is valid, and no starter code passes on its own.
- `backend/tests/test_learning_extensions.py` runs scenarios 1–6 and 8 end to end against Supabase and Judge0, using a throwaway student that is deleted afterwards.
