# AI Coding Mentor – Supabase & Ollama Integration Guide

This guide explains how to connect your **AI Coding Mentor** application to a hosted **Supabase PostgreSQL database** and your local **Ollama LLM** instance.

---

## Part 1: How the Database Connects to Your Website

The application uses an enterprise-grade three-tier architecture:

```
┌─────────────────────────────────┐
│     React + Monaco Frontend     │  (Browser at http://127.0.0.1:8000)
└────────────────┬────────────────┘
                 │  REST API Calls (/api/...)
                 ▼
┌─────────────────────────────────┐
│        FastAPI Backend          │  (Python + psycopg Connection Pool)
└───────┬─────────────────┬───────┘
        │                 │
        │ PostgreSQL URI  │ HTTP (Port 11434)
        ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│    Supabase     │ │  Local Ollama   │
│   (PostgreSQL)  │ │  (gemma3 / etc) │
└─────────────────┘ └─────────────────┘
```

### Security & Connectivity Principles:
1. **Frontend Isolation**: The React frontend never connects directly to Supabase and never stores database passwords or service role keys.
2. **Server-Side Connection Pooling**: The FastAPI backend manages an asynchronous connection pool (`psycopg_pool`) connected to Supabase PostgreSQL.
3. **Automatic Persistence**: When a student registers, runs code, submits challenges, or unlocks achievements in the website UI, the backend executes transactions directly on your Supabase tables.

---

## Part 2: Step-by-Step Supabase Setup

### Step 1: Create a Free Supabase Project
1. Go to [https://supabase.com](https://supabase.com) and sign in (or create a free account).
2. Click **New Project**.
3. Choose an organization, enter a project name (e.g., `ai-coding-mentor`), set a strong database password, and select your nearest region.
4. Click **Create new project** and wait ~1–2 minutes for the database to provision.

---

### Step 2: Initialize Database Tables & Seed Data
You have a ready-to-run schema file: `SUPABASE_SCHEMA.sql` in the project root.

1. In your Supabase Dashboard, click on **SQL Editor** in the left sidebar.
2. Click **+ New Query**.
3. Open the file `SUPABASE_SCHEMA.sql` on your computer, copy its entire contents, and paste them into the Supabase SQL Editor.
4. Click **Run** (or press `Ctrl+Enter`).
5. You will see `Success. No rows returned`.
6. Click on **Table Editor** in the left sidebar to verify all 11 tables have been created:
   - `users`
   - `student_profiles`
   - `coding_challenges` (pre-seeded with 5 foundational challenges)
   - `code_submissions`
   - `execution_results`
   - `ai_feedback`
   - `learning_assessments`
   - `student_skills`
   - `learning_history`
   - `achievements` (pre-seeded with 6 milestone badges)
   - `student_achievements`

---

### Step 3: Get Your Supabase Connection String (URI)
1. In your Supabase Dashboard, click the **Connect** button at the top header (or navigate to **Project Settings** -> **Database**).
2. Under **Connection string**, select **URI**.
3. Choose the **Session Pooler** (port `5432`) or **Transaction Pooler** (port `6543`).
   > **Tip:** Use the Session pooler URI as it supports standard IPv4 networks:
   ```text
   postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[YOUR-REGION].pooler.supabase.com:5432/postgres?sslmode=require
   ```
4. Replace `[YOUR-PASSWORD]` with the database password you created in Step 1.

---

### Step 4: Configure Your Website Backend
1. Open the file `backend/.env` (or copy from `backend/.env.example` if it doesn't exist yet).
2. Set the `DATABASE_URL` variable to your connection string:

```env
# ==========================================
# AI CODING MENTOR - ENVIRONMENT CONFIGURATION
# ==========================================

# Database - Supabase PostgreSQL Connection String
DATABASE_URL=postgresql://postgres.yourprojectref:yourpassword@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require

# Supabase REST API credentials (Optional)
SUPABASE_URL=https://yourprojectref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# Local LLM with Ollama
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest
```

---

## Part 3: Local LLM with Ollama

Your system already has Ollama installed at `D:\Ollama\ollama.exe` and running on `http://localhost:11434` with `gemma3:latest` and `gemma4:12b`!

### How the Local LLM Operates:
- When you ask the **AI Mentor** in the playground (Learning Mode, Debugging Mode, or Hint Mode) or run the **AI Code Autopsy**, the backend sends a structured prompt directly to `http://localhost:11434/api/chat`.
- Ollama processes the prompt locally on your GPU/CPU with zero API costs and zero external network latency.
- It returns strictly formatted pedagogical JSON, and the mentor displays progressive hints and loop breakdowns to the student.

### Changing or Pulling Other Models:
To switch models, pull any coding or chat model via your terminal:
```powershell
# Examples:
ollama run gemma3:latest
ollama run deepseek-coder:6.7b
ollama run qwen2.5-coder
ollama run llama3.2
```
Then update `backend/.env`:
```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest   # or deepseek-coder:6.7b / qwen2.5-coder
```

---

## Part 4: Launching & Testing the Platform

### Start the Application:
From the workspace root directory:
```powershell
.\.venv\Scripts\python.exe run_app.py
```

### Access Your Application:
- **Web Application UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **System Health Endpoint:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

When visiting `/api/health`, you will observe:
```json
{
  "status": "healthy",
  "app": "AI Coding Mentor API",
  "version": "1.0.0",
  "environment": "development",
  "execution_provider": "Isolated Local Sandbox (Judge0 credentials unconfigured)",
  "ai_provider": "ollama"
}
```

---

## Part 5: Verification Checklist

1. **Database Check**:
   - Register a new student account in the UI.
   - Go to your Supabase Dashboard -> **Table Editor** -> `users`.
   - Your newly registered user will appear immediately in Supabase!
2. **Coding Challenge Check**:
   - Go to the Playground tab and solve `Sum of List Elements`.
   - Click **Submit Solution**.
   - Check the `code_submissions` and `student_skills` tables in Supabase to see real-time updates.
3. **Local LLM Check**:
   - In the right sidebar of the Playground, select **Learning** or **Debugging** mode.
   - Click **Explain My Code**.
   - Your local Ollama model will generate instant pedagogical hints without hitting external cloud APIs.
