# AI Coding Mentor: demo script and judge Q&A

5 minutes live, then 3 minutes of questions. Deck: `AI_Coding_Mentor_Overview.pptx` (15 slides).

Replace **[Member 1]**, **[Member 2]**, **[Member 3]** with your names, and adjust the role split in section 5 if it does not match who did what.

---

## Before you walk up (checklist)

1. Backend running: `.\.venv\Scripts\python.exe run_app.py`, then open `http://127.0.0.1:8000`.
2. Ollama running with `gemma3` pulled (the mentor falls back to its rule engine if it is not, so the demo still works).
3. Judge0 reachable (`JUDGE0_API_URL` is set in `backend/.env`). Submit one C task beforehand to warm it up.
4. Sign in with a demo account that already has some XP, a streak and a generated roadmap. A fresh account shows empty pages.
5. Browser at 100% zoom, light theme, one tab on the landing page, one tab already signed in on Academy.
6. Have the wrong Python solution (below) on the clipboard.
7. The deck open on slide 1 in a second window.

Wrong solution to paste in the Playground ("Sum of List Elements"):

```python
def sum_numbers(numbers):
    total = 0
    for i in range(len(numbers)):
        total += i
    return total
```

It adds the index instead of the value, which is exactly the mistake the Code Autopsy is built to catch.

---

## Timing plan (5:00)

| Time | Who | What | Screen |
|---|---|---|---|
| 0:00–0:35 | Member 1 | Problem and why we chose it | Slides 1–2 |
| 0:35–1:00 | Member 1 | What we built, in one breath | Slide 3 |
| 1:00–1:50 | Member 2 | Demo 1: landing, course path, lesson, XP | App |
| 1:50–2:40 | Member 2 | Demo 2: C task compiled by Judge0 | App |
| 2:40–3:40 | Member 3 | Demo 3: wrong answer, autopsy, hints, tracer | App |
| 3:40–4:05 | Member 3 | Demo 4: dashboard, roadmap, trophies | App |
| 4:05–4:35 | Member 2 | Architecture and Judge0 in 30 seconds | Slides 7–8 |
| 4:35–5:00 | Member 1 | What makes it different, close | Slides 6, 15 |

Slides 4, 5, 9–14 are not presented. They are there for the judges to read and for you to jump to during Q&A.

---

## The script

### 0:00 — Opening (Member 1, slides 1–2)

> "Good morning. We are team [team name], and this is AI Coding Mentor.
>
> Everyone in a programming class learns at a different speed, but the course moves at one speed. And when your code breaks, the feedback comes days later, in a marked lab sheet, long after you have forgotten what you were thinking.
>
> We chose this problem because we lived it. In our own C and DBMS labs, the students who got stuck early stayed stuck. The tools we had either just said 'wrong answer', or, with a chatbot, handed over the full solution. Neither one teaches you anything."

### 0:35 — What we built (Member 1, slide 3)

> "So we built a platform that does three things. It makes practice feel like a game. It runs your code instantly in a real sandbox. And it has a mentor that adapts to you and gives hints, never the answer. Let us show you."

### 1:00 — Demo 1: the path (Member 2, app)

*Landing page.*

> "This is what a new student sees. They can try a question before signing up."

*Click `3`, click Check, click Keep going.*

> "Now the Academy. Every course is a path. Green nodes are lessons, blue are practice tasks, gold is the level assessment. You cannot skip ahead: level two unlocks only when you pass the level one assessment."

*Open the current lesson, scroll briefly, click Mark lesson complete.*

> "I finish a lesson, and I get XP straight away. Watch the top bar: streak, level, XP. Every hundred XP is a new level."

### 1:50 — Demo 2: real code, really compiled (Member 2, app)

*Back to the path, open the next blue task (a C task). Type or paste the solution, click Submit.*

> "This is a real C program. When I press Submit, the code goes to Judge0, an open-source code execution engine. It compiles it with GCC inside an isolated sandbox, feeds it hidden test input, and compares the output."

*Confetti, XP pop.*

> "All tests pass, XP is awarded, and it is awarded only once, so nobody can farm points by resubmitting."

### 2:40 — Demo 3: getting stuck (Member 3, app)

*Playground tab. Paste the wrong solution. Click Submit.*

> "Now the part we care about most: what happens when a student is wrong.
>
> This solution fails. A normal judge stops here. We do three more things."

*Open AI Code Autopsy.*

> "One: the Code Autopsy. It finds the root cause, here that the loop adds the index instead of the value, and shows it iteration by iteration."

*Open Visual Execution Tracer, press play for two or three steps.*

> "Two: the visual tracer. The student can step through their own code and watch each variable change."

*Mentor panel, Hints mode, reveal the first hint.*

> "Three: the mentor. It runs on a local Gemma model through Ollama. It gives a conceptual hint first, then a directional one, then a guided one. It never prints the solution. And if the student keeps failing, the system notices the strain and offers help on its own."

*If time: point at the Déjà Vu panel.*

> "It also remembers. If I make this same mistake next week, it tells me I have made it before and shows me how I fixed it last time."

### 3:40 — Demo 4: the adaptive side (Member 3, app)

*Dashboard.*

> "Everything feeds the dashboard: skill mastery per topic, weak areas, and a Programming DNA profile across six dimensions."

*Roadmap tab, then Achievements tab, two seconds each.*

> "From that, it builds a thirty-day roadmap for this student, and the trophy shelf tracks what they have earned."

### 4:05 — How it works (Member 2, slides 7–8)

> "Under the hood: a React and TypeScript front end with the Monaco editor. A FastAPI back end. Supabase PostgreSQL for data. Student code never runs inside our server. C and Python go to Judge0, SQL runs in a throwaway in-memory database, and the tracer runs in its own capped process. The mentor is a local model with a rule-based fallback, so it works offline."

### 4:35 — Close (Member 1, slides 6 and 15)

> "What makes this different: it teaches instead of answering, it remembers your mistakes, it adapts the plan to you, and it makes you want to come back tomorrow.
>
> That is AI Coding Mentor. Thank you. We would love your questions."

---

## If something breaks on stage

| Problem | What to do |
|---|---|
| Judge0 slow or down | Say "the execution engine is remote, so here is a run from earlier" and show the Dashboard history; continue with the Python Playground, which is the path you rehearsed most |
| Ollama not responding | Keep going: the rule-based mentor answers instead. Say "this is our offline fallback" |
| Database slow to load | Talk over slide 7 (architecture) while it loads |
| Playground starter code shows `\n` on one line | Select all and paste your prepared code; do not type from scratch |
| Out of time at 4:00 | Skip Demo 4, go straight to slide 7 |

---

## Content for each of the twelve points

### 1. Why we chose this project

- Students learn at different speeds; courses run at one speed.
- Debugging feedback arrives late, after the thinking is forgotten.
- Existing tools sit at two extremes: judges that only say pass or fail, and chatbots that give the whole answer.
- We saw it in our own C and DBMS labs, so we could test the idea on real coursework.
- It needs both software engineering and learning design, which made it a good team project.

### 2. Implementation plan

| Phase | What we built |
|---|---|
| 1. Foundation | Accounts with JWT, Supabase PostgreSQL schema, FastAPI skeleton, React shell |
| 2. Core loop | Monaco playground, code execution through Judge0 with a local sandbox fallback, challenges with test cases |
| 3. Intelligence | AI mentor with three modes, Code Autopsy, visual execution tracer, adaptive mastery engine, Programming DNA |
| 4. Learning extensions | Coding Academy (C, DBMS & SQL), Mistake Memory and Déjà Vu, learning-strain assistance, 30-day roadmap |
| 5. Game layer and polish | Course path, XP and levels, streaks, trophies, landing page, light and dark themes, tests |

### 3. Research behind the features

| We studied | It became |
|---|---|
| Scaffolding: help should be just enough, then withdrawn | Three-step hints: conceptual, directional, guided. Never the solution |
| Mastery learning: move on only after you can show the skill | Levels locked behind assessments |
| Common novice errors (off-by-one, index vs value, missing base case) | Mistake signatures in Code Autopsy and Mistake Memory |
| Spaced review of weak material | Roadmap schedules review days for concepts you struggled with |
| Program visualisation tools and Python's `sys.settrace` hook | Step-by-step visual tracer |
| Judge0 documentation and how online judges sandbox code | Execution service, limits, base64 transport |
| Game mechanics in learning apps: streaks, XP, visible paths | The game layer |
| Running small language models locally (Ollama, Gemma 3) | Private mentor with no API cost |

### 4. Unique features

1. **Hints, not answers.** The mentor is instructed never to output the solution, and hints are disabled during assessments.
2. **Code Autopsy.** Names the misconception and shows it loop iteration by loop iteration.
3. **Mistake Memory and Déjà Vu.** Classifies each failure; recognises a repeat or a related mistake; replays your own earlier fix.
4. **Learning-strain detection.** A transparent score from consecutive failures, repeated mistakes, hint requests and time on task. Offers help before you ask.
5. **Visual execution tracer.** Step through your own Python and watch variables change.
6. **Personalised 30-day roadmap.** Built from your progress, mistakes and weak skills.
7. **Programming DNA.** Six measured dimensions and an archetype.
8. **Works offline.** Local model, plus a rule-based mentor if the model is off.

### 5. Team roles (edit to match your team)

| Member | Role | Owned |
|---|---|---|
| [Member 1] | Front end and game design | React and TypeScript UI, Monaco integration, course path, score bar, landing page, themes |
| [Member 2] | Back end and code execution | FastAPI services, Judge0 client, sandboxes and tracer, Supabase schema, authentication |
| [Member 3] | AI mentor and learning logic | Ollama integration and prompts, autopsy rules, Mistake Memory, strain score, roadmap, course content, testing |

### 6. Advantages over existing tools

| | Typical online judge | General AI chatbot | Video course | AI Coding Mentor |
|---|---|---|---|---|
| Runs and tests your code | Yes | No | No | Yes |
| Explains why it failed | No | Yes | No | Yes |
| Withholds the full answer | n/a | No | n/a | Yes |
| Remembers your past mistakes | No | No | No | Yes |
| Adapts the plan to you | No | No | No | Yes |
| Game progression | Sometimes | No | No | Yes |
| Works without internet AI | n/a | No | n/a | Yes |

### 7. Pipeline and architecture

**Layers**

```
Student browser
  React 19 + TypeScript + Vite, Monaco editor
        |  REST / JSON, JWT in the Authorization header
        v
FastAPI back end (Python)
  auth | challenges | academy | execution | ai_mentor
  adaptive_learning | mistake_memory | assistance | roadmap | analytics | achievements
        |                    |                         |
        v                    v                         v
  Code execution        AI mentor                 Supabase PostgreSQL
  - Judge0 (C, Python)  - Ollama, Gemma 3         users, profiles, challenges,
  - SQL sandbox         - rule engine fallback    submissions, skills, courses,
    (in-memory SQLite)                            mistakes, roadmaps, achievements
  - Python tracer
    (sys.settrace)
```

**One submission, end to end**

1. Student writes code in Monaco and presses Submit.
2. The front end sends code and task id to FastAPI with the JWT.
3. The execution service runs it against each test case in Judge0 (or the SQL sandbox).
4. Outputs are compared with the expected results; hidden tests stay hidden.
5. **Pass:** XP is awarded once, skill mastery rises, achievements are checked, the next node unlocks.
6. **Fail:** the mistake is classified and stored, Déjà Vu checks for a repeat, the strain score updates, a hint is offered.
7. Dashboard, DNA profile and roadmap are recalculated from the new data.
8. The UI shows the result, the XP pop and, on a pass, confetti.

### 8. How we gamified it

| Mechanic | How it works in the app |
|---|---|
| XP | Lessons, tasks, assessments, challenges and roadmap days pay XP, once each |
| Levels | 100 XP per level; level badge and XP meter always visible |
| Streak | Counts consecutive days of practice |
| Course path | Winding path of nodes; a bouncing "Start" marks your next step |
| Locks and gates | A level opens only after the previous assessment is passed |
| Trophies | Six milestone achievements plus a badge for each completed course |
| Instant reward | "+XP" pop, level-up banner, confetti on a pass |
| Difficulty tiers | Beginner, Intermediate, Advanced, with larger XP for harder work |
| Daily quest | The roadmap gives one verified task per day |
| Fair play | XP only for verified work; hints off in assessments |

### 9. Tech stack and where each piece is used

| Layer | Technology | Used for |
|---|---|---|
| UI | React 19, TypeScript, Vite | Single-page app, all screens |
| Editor | Monaco Editor | Code editing in Playground and Academy tasks |
| UI extras | lucide-react, canvas-confetti, Nunito font | Icons, celebrations, type |
| API | FastAPI, Uvicorn, Pydantic | REST endpoints, validation, serving the built app |
| Auth | PBKDF2-SHA256 hashing, JWT (HS256) | Accounts and protected routes |
| Database | Supabase PostgreSQL via psycopg 3 with a connection pool | All persistent data |
| Code execution | Judge0 | Compiling and running C and Python against tests |
| SQL exercises | SQLite in memory, separate process | Safe SQL practice |
| Tracing | Python `sys.settrace` in a child process | Visual debugger |
| AI | Ollama running Gemma 3 | Mentor, autopsy text, roadmap tips |
| Fallback AI | Rule-based engine in Python | Works with no model |
| HTTP | httpx | Calls to Judge0 and Ollama |
| Testing | Python test suites, TypeScript compiler, oxlint | Back-end, API and front-end checks |

### 10. Questions the judges may ask

**Q1. How is this different from just asking ChatGPT?**
A chatbot gives you the finished code. Ours is told never to output the solution: it gives three graded hints. It also actually runs your code, knows which test failed, and remembers your earlier mistakes. A chatbot starts from zero every time.

**Q2. Is it safe to run code that students submit?**
Student code never runs inside our server process. C and Python go to Judge0, which runs each submission in an isolated sandbox with a 5-second CPU limit and a 128 MB memory limit. SQL runs in a separate process on a throwaway in-memory database, with `ATTACH` and `PRAGMA` blocked. The tracer runs in a child process capped at 150 steps and 3.5 seconds.

**Q3. What happens if Judge0 is down?**
The execution service has a fallback: an isolated local subprocess with a 4-second timeout that first checks the code's syntax tree and blocks dangerous imports such as `os`, `subprocess` and `socket`. That fallback covers Python; C needs Judge0.

**Q4. How does the "adaptive" part work? Is it machine learning?**
It is rule-based on purpose, so every decision can be explained. Skill mastery is calculated from your solve ratio, problems solved and error count per topic. The strain score adds up signals such as consecutive failures and repeated mistakes. The roadmap is built from course progress, weak skills and recorded mistakes. The language model only writes the wording.

**Q5. Why a local model instead of a cloud API?**
Three reasons: student code stays on the machine, there is no per-request cost, and it works without internet. The trade-off is that a small model is less capable, which is why the facts come from our rule engine and the model only phrases them.

**Q6. Can the AI give a wrong hint?**
It can phrase things poorly, but the diagnosis comes from actual execution results and the rule engine, not from the model guessing. If the model is unavailable or returns something unusable, the rule-based response is shown.

**Q7. How do you stop students gaming the XP?**
XP for any item is awarded once, enforced by a unique constraint in the database. XP is only given for work that was verified by running it. Hints are disabled during assessments.

**Q8. How does it recognise a repeated mistake?**
Each failure is turned into a signature: for Python from the autopsy rules, for C from compiler and runtime evidence, for SQL from the error and result comparison. Same signature means a repeat; same concept means related.

**Q9. Will it scale to a full class?**
The API is stateless with JWT, and the database uses a connection pool, so the web tier can be scaled out. The bottlenecks are Judge0 and the model. Judge0 is designed to scale with more workers; the model would move to a shared GPU server. We have not load-tested it yet.

**Q10. Which languages are supported?**
Python in the Playground, C and SQL in the Academy. The Judge0 client already maps JavaScript, C++ and Java, so adding them is mostly content and test cases.

**Q11. How did you test it?**
A back-end suite of eight tests for the engines, an API integration suite, an end-to-end suite for the learning extensions, and a content validator that checks every C reference solution passes on Judge0 and that no starter code passes by itself.

**Q12. What was the hardest part?**
Making failure useful. Getting from "wrong answer" to "you added the index instead of the value, and you did the same thing on Tuesday" took the most design work.

**Q13. Does gamification actually help, or is it decoration?**
We tied every reward to verified learning: you only earn XP for code that passed. The path and the locks also carry real structure, because they enforce the order of the course.

**Q14. Who is the target user?**
First- and second-year students learning C, SQL and Python, and teachers who want practice that marks itself.

### 11. Judge0: what it is, how it works, how we use it

**What it is.** Judge0 is an open-source online code execution system. You send it source code over a REST API; it compiles and runs the code in a sandbox and returns the output. It supports more than 60 languages and can be self-hosted or used as a hosted service.

**How it works inside.**
1. The API server receives a submission and puts it in a queue.
2. A worker picks it up and runs it inside `isolate`, a Linux sandbox that cuts off network and file access and enforces CPU time and memory limits.
3. The worker compiles (for compiled languages), runs the program with the given standard input, and captures standard output, standard error and compiler output.
4. It records a status: In Queue, Processing, Accepted, Wrong Answer, Time Limit Exceeded, Compilation Error, Runtime Error or Internal Error.

**How we use it** (`backend/app/execution/judge0_client.py`).
- One call: `POST /submissions?base64_encoded=true&wait=true`.
- We send `source_code`, `language_id`, `stdin`, `cpu_time_limit: 5.0` and `memory_limit: 128000` (KB).
- Language ids: C (GCC 9.2.0) is 50, Python 3 is 71. JavaScript 63, C++ 54 and Java 62 are mapped for later.
- Everything is base64-encoded both ways, because compiler messages are not always valid UTF-8.
- `wait=true` returns the result in the same request, so the student sees it immediately.
- We read `stdout`, `stderr`, `compile_output`, `time` and `status`. Status id 3 means Accepted.
- For each test case we run the code, then compare its output with the expected output ourselves.
- Authentication: `X-Auth-Token` for a self-hosted instance, RapidAPI headers for the hosted one.

**Why Judge0.** Writing a safe compiler sandbox is a project in itself. Judge0 gives real GCC, real limits and many languages behind one API, and it is open source.

### 12. Limitations and future scope

**Limitations today**
- The Playground runs Python only; C and SQL are available inside the Academy.
- Two courses so far: C Programming and DBMS & SQL.
- The mentor needs Ollama running locally; a small model sometimes words things awkwardly.
- C execution depends on a reachable Judge0 server.
- The visual tracer is Python only and stops at 150 steps.
- No leaderboard, teams or teacher view yet.
- Not load-tested with a full class.

**Future scope**
- More languages in the Playground: JavaScript, C++, Java (already mapped in the Judge0 client).
- Leaderboards and weekly leagues; friends and class groups.
- Teacher dashboard: class-wide weak topics, assignment creation.
- More courses: data structures, Python, Java.
- Self-hosted Judge0 cluster for exams.
- Installable mobile app (PWA) with offline lessons.
- Voice explanations and regional-language support.
- A model fine-tuned on novice mistakes.
