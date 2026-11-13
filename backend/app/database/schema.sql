-- =====================================================================
-- AI Coding Mentor – Supabase (PostgreSQL) schema
-- Mirrors backend/app/database/session.py (11 tables + indexes + seeds).
-- Executed automatically by init_database() on startup (idempotent).
-- You can also paste it into Supabase Dashboard -> SQL Editor -> Run.
--
-- Notes:
--  * IDs stay TEXT (the backend generates its own string IDs).
--  * JSON fields stay TEXT because the backend stores json.dumps() strings
--    and json.loads() them on read.
--  * The app uses its own auth (users table), not Supabase Auth.
--  * RLS is enabled with no policies, so the public anon key cannot read
--    or write these tables. The backend should connect with the database
--    connection string or the service role key, which bypass RLS.
-- =====================================================================

-- 1. users
CREATE TABLE IF NOT EXISTS public.users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT DEFAULT 'student',
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

-- 2. student_profiles
CREATE TABLE IF NOT EXISTS public.student_profiles (
    user_id            TEXT PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    current_level      INTEGER DEFAULT 1,
    total_xp           INTEGER DEFAULT 0,
    streak_days        INTEGER DEFAULT 0,
    last_active_date   TEXT,
    preferred_language TEXT DEFAULT 'python',
    bio                TEXT DEFAULT ''
);

-- 3. coding_challenges
CREATE TABLE IF NOT EXISTS public.coding_challenges (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    slug          TEXT UNIQUE NOT NULL,
    topic         TEXT NOT NULL,
    difficulty    TEXT NOT NULL,
    description   TEXT NOT NULL,
    initial_code  TEXT NOT NULL,
    solution_code TEXT,
    test_cases    TEXT NOT NULL,          -- JSON array of {input, expected_output, hidden}
    constraints   TEXT,
    hints         TEXT,                   -- JSON array of progressive hints
    xp_reward     INTEGER DEFAULT 50,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- 4. code_submissions
CREATE TABLE IF NOT EXISTS public.code_submissions (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    challenge_id   TEXT REFERENCES public.coding_challenges(id) ON DELETE SET NULL,
    code           TEXT NOT NULL,
    language       TEXT NOT NULL,
    status         TEXT NOT NULL,         -- Accepted, Wrong Answer, Runtime Error, Syntax Error, Time Limit Exceeded
    execution_time DOUBLE PRECISION DEFAULT 0.0,
    memory_used    INTEGER DEFAULT 0,
    error_type     TEXT,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 5. execution_results
CREATE TABLE IF NOT EXISTS public.execution_results (
    id                 TEXT PRIMARY KEY,
    submission_id      TEXT UNIQUE NOT NULL REFERENCES public.code_submissions(id) ON DELETE CASCADE,
    stdout             TEXT,
    stderr             TEXT,
    compile_output     TEXT,
    exit_code          INTEGER,
    status_description TEXT,
    executed_at        TIMESTAMPTZ DEFAULT now()
);

-- 6. ai_feedback
CREATE TABLE IF NOT EXISTS public.ai_feedback (
    id                   TEXT PRIMARY KEY,
    submission_id        TEXT REFERENCES public.code_submissions(id) ON DELETE SET NULL,
    user_id              TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mode                 TEXT NOT NULL,   -- learning, debugging, hint, autopsy
    summary              TEXT NOT NULL,
    detailed_explanation TEXT NOT NULL,
    hints_given          TEXT,            -- JSON array
    misconceptions       TEXT,            -- JSON array
    suggested_topics     TEXT,            -- JSON array
    created_at           TIMESTAMPTZ DEFAULT now()
);

-- 7. learning_assessments
CREATE TABLE IF NOT EXISTS public.learning_assessments (
    id                 TEXT PRIMARY KEY,
    user_id            TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    topic              TEXT NOT NULL,
    calculated_score   DOUBLE PRECISION DEFAULT 0.0,
    strengths          TEXT,              -- JSON array
    weaknesses         TEXT,              -- JSON array
    recommended_action TEXT,
    evaluated_at       TIMESTAMPTZ DEFAULT now()
);

-- 8. student_skills
CREATE TABLE IF NOT EXISTS public.student_skills (
    id                 TEXT PRIMARY KEY,
    user_id            TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill_name         TEXT NOT NULL,
    mastery_level      DOUBLE PRECISION DEFAULT 10.0,  -- 0 to 100%
    problems_solved    INTEGER DEFAULT 0,
    problems_attempted INTEGER DEFAULT 0,
    error_count        INTEGER DEFAULT 0,
    last_practiced     TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, skill_name)
);

-- 9. learning_history
CREATE TABLE IF NOT EXISTS public.learning_history (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,             -- challenge_solved, hint_viewed, autopsy_run, streak_gained, level_up
    details    TEXT,
    xp_earned  INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 10. achievements
CREATE TABLE IF NOT EXISTS public.achievements (
    id                  TEXT PRIMARY KEY,
    code                TEXT UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    badge_icon          TEXT NOT NULL,
    xp_reward           INTEGER DEFAULT 100,
    milestone_threshold INTEGER DEFAULT 1
);

-- 11. student_achievements
CREATE TABLE IF NOT EXISTS public.student_achievements (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    achievement_id TEXT NOT NULL REFERENCES public.achievements(id) ON DELETE CASCADE,
    unlocked_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, achievement_id)
);

-- ---------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------
DO $$ BEGIN IF to_regclass('public.idx_submissions_user') IS NULL THEN CREATE INDEX idx_submissions_user ON public.code_submissions(user_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_submissions_challenge') IS NULL THEN CREATE INDEX idx_submissions_challenge ON public.code_submissions(challenge_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_skills_user') IS NULL THEN CREATE INDEX idx_skills_user ON public.student_skills(user_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_history_user') IS NULL THEN CREATE INDEX idx_history_user ON public.learning_history(user_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_feedback_user') IS NULL THEN CREATE INDEX idx_feedback_user ON public.ai_feedback(user_id); END IF; END $$;
-- Challenge ownership: student-created challenges are private to their creator
-- unless shared. Seeded challenges (created_by NULL) stay public. Added only if
-- missing, because ALTER TABLE takes an exclusive lock.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_schema = 'public' AND table_name = 'coding_challenges' AND column_name = 'created_by') THEN
    ALTER TABLE public.coding_challenges
      ADD COLUMN created_by TEXT REFERENCES public.users(id) ON DELETE CASCADE,
      ADD COLUMN visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('public', 'private'));
  END IF;
END $$;

-- ---------------------------------------------------------------------
-- Seed data: achievements
-- ---------------------------------------------------------------------
INSERT INTO public.achievements (id, code, title, description, badge_icon, xp_reward, milestone_threshold) VALUES
('ach_first_code',   'FIRST_BLOOD',        'First Code Executed', 'Run your first program in the playground',              'Play',   50,  1),
('ach_first_solve',  'FIRST_SOLVE',        'Bug Hunter',          'Successfully pass all test cases for a challenge',      'Award',  100, 1),
('ach_autopsy',      'FORENSIC_CODER',     'Code Autopsy',        'Run an AI autopsy to diagnose a conceptual mistake',    'Search', 75,  1),
('ach_visual_trace', 'X_RAY_VISION',       'Visual Explorer',     'Step through code execution in the Visual Debugger',    'Eye',    75,  1),
('ach_three_streak', 'CONSISTENT_THINKER', '3-Day Streak',        'Practice coding 3 days in a row',                       'Flame',  150, 3),
('ach_loops_master', 'LOOP_MASTER',        'Master of Loops',     'Solve 5 challenges on loops and iterations',            'Repeat', 200, 5)
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------
-- Seed data: coding challenges
-- ---------------------------------------------------------------------
INSERT INTO public.coding_challenges
    (id, title, slug, topic, difficulty, description, initial_code, solution_code, test_cases, constraints, hints, xp_reward)
VALUES
(
    'ch_sum_list', 'Sum of List Elements', 'sum-of-list', 'Loops & Lists', 'Beginner',
    'Write a function `sum_numbers(numbers)` that takes a list of integers and returns their total sum. If the list is empty, return 0.',
    E'def sum_numbers(numbers):\n    # Write your solution here\n    pass\n',
    E'def sum_numbers(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total\n',
    '[{"input": "[1, 2, 3, 4, 5]", "expected_output": "15", "hidden": false}, {"input": "[-2, 5, 10]", "expected_output": "13", "hidden": false}, {"input": "[]", "expected_output": "0", "hidden": true}, {"input": "[100]", "expected_output": "100", "hidden": true}]',
    'Input is a list of integers. Length between 0 and 1000.',
    '["Consider initializing an accumulator variable like `total = 0` before the loop.", "Loop through each item directly using `for num in numbers:`, not just the index.", "Make sure to return the accumulated total after the loop finishes, not inside it."]',
    50
),
(
    'ch_find_max', 'Find Maximum Number', 'find-maximum-number', 'Conditions', 'Beginner',
    'Write a function `find_max(numbers)` that finds and returns the largest number in a non-empty list of integers without using the built-in `max()` function.',
    E'def find_max(numbers):\n    # Do not use Python''s built-in max()\n    pass\n',
    E'def find_max(numbers):\n    highest = numbers[0]\n    for n in numbers:\n        if n > highest:\n            highest = n\n    return highest\n',
    '[{"input": "[3, 7, 2, 9, 4]", "expected_output": "9", "hidden": false}, {"input": "[-10, -5, -20]", "expected_output": "-5", "hidden": false}, {"input": "[42]", "expected_output": "42", "hidden": true}]',
    'List will contain at least one integer. Values can be negative.',
    '["Initialize your maximum tracker to the first element `numbers[0]` instead of 0 (which breaks for negative numbers).", "Compare each number against your tracker using an `if` statement.", "Update the tracker only when the current element is greater."]',
    60
),
(
    'ch_reverse_string', 'Reverse a String', 'reverse-string', 'Strings', 'Beginner',
    'Write a function `reverse_string(text)` that returns the reversed version of the given string.',
    E'def reverse_string(text):\n    # Write your solution here\n    pass\n',
    E'def reverse_string(text):\n    return text[::-1]\n',
    '[{"input": "''hello''", "expected_output": "''olleh''", "hidden": false}, {"input": "''Python''", "expected_output": "''nohtyP''", "hidden": false}, {"input": "''''", "expected_output": "''''", "hidden": true}]',
    'Input is a standard string. May contain spaces and punctuation.',
    '["In Python, strings can be reversed using extended slicing or a backwards loop.", "Check slice syntax `string[::-1]` or building a new string prepending characters."]',
    40
),
(
    'ch_count_vowels', 'Count Vowels in String', 'count-vowels', 'Strings & Conditions', 'Beginner',
    'Write a function `count_vowels(s)` that counts how many vowels (a, e, i, o, u) exist in a string, case-insensitively.',
    E'def count_vowels(s):\n    # Count both lowercase and uppercase vowels\n    pass\n',
    E'def count_vowels(s):\n    vowels = set(''aeiouAEIOU'')\n    return sum(1 for char in s if char in vowels)\n',
    '[{"input": "''Algorithm''", "expected_output": "3", "hidden": false}, {"input": "''sky''", "expected_output": "0", "hidden": false}, {"input": "''AEIOU''", "expected_output": "5", "hidden": true}]',
    'String length 0 to 500.',
    '["Convert the input to lowercase or check against both lowercase and uppercase vowels.", "Use the `in` keyword to test if a character is in a vowel string/set like `''aeiou''`."]',
    50
),
(
    'ch_fibonacci', 'Nth Fibonacci Number', 'nth-fibonacci', 'Recursion & Functions', 'Intermediate',
    'Write a function `fibonacci(n)` that returns the nth Fibonacci number, where F(0) = 0 and F(1) = 1.',
    E'def fibonacci(n):\n    # Return the nth Fibonacci number\n    pass\n',
    E'def fibonacci(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n',
    '[{"input": "0", "expected_output": "0", "hidden": false}, {"input": "1", "expected_output": "1", "hidden": false}, {"input": "6", "expected_output": "8", "hidden": false}, {"input": "10", "expected_output": "55", "hidden": true}]',
    '0 <= n <= 30',
    '["Identify your base cases: what should happen when n is 0 or 1?", "An iterative loop using two variables `a, b` is O(N) time and avoids recursion stack depth limits."]',
    80
)
ON CONFLICT DO NOTHING;

-- =====================================================================
-- LEARNING EXTENSIONS: Coding Academy, Mistake Memory, Learning-Strain
-- Assistance and the 30-Day Roadmap. Additive only: nothing above is
-- altered. Course content is seeded from app/academy/content.py.
-- =====================================================================

-- Course completion badges (reuse the existing achievements table)
INSERT INTO public.achievements (id, code, title, description, badge_icon, xp_reward, milestone_threshold) VALUES
('ach_course_c',   'COURSE_C_COMPLETE',   'C Programming - Course Completed', 'Passed every level assessment and the final assessment of the C Programming course', 'GraduationCap', 200, 1),
('ach_course_sql', 'COURSE_SQL_COMPLETE', 'DBMS & SQL - Course Completed',    'Passed every level assessment and the final assessment of the DBMS & SQL course',    'Database',      200, 1)
ON CONFLICT DO NOTHING;

-- 12. courses
CREATE TABLE IF NOT EXISTS public.courses (
    id                        TEXT PRIMARY KEY,
    slug                      TEXT UNIQUE NOT NULL,
    title                     TEXT NOT NULL,
    description               TEXT NOT NULL,
    language                  TEXT NOT NULL,          -- execution language: c, sql
    icon                      TEXT DEFAULT 'BookOpen',
    sort_order                INTEGER DEFAULT 0,
    completion_xp             INTEGER DEFAULT 200,
    completion_achievement_id TEXT REFERENCES public.achievements(id) ON DELETE SET NULL,
    created_at                TIMESTAMPTZ DEFAULT now()
);

-- 13. course_levels
CREATE TABLE IF NOT EXISTS public.course_levels (
    id           TEXT PRIMARY KEY,
    course_id    TEXT NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    level_number INTEGER NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    UNIQUE (course_id, level_number)
);

-- 14. course_lessons
CREATE TABLE IF NOT EXISTS public.course_lessons (
    id                TEXT PRIMARY KEY,
    level_id          TEXT NOT NULL REFERENCES public.course_levels(id) ON DELETE CASCADE,
    sort_order        INTEGER NOT NULL,
    title             TEXT NOT NULL,
    summary           TEXT NOT NULL,
    content           TEXT NOT NULL,                  -- lightweight markdown
    concept           TEXT NOT NULL,
    estimated_minutes INTEGER DEFAULT 15,
    xp_reward         INTEGER DEFAULT 10
);

-- 15. course_tasks (practice tasks and level/final assessments)
CREATE TABLE IF NOT EXISTS public.course_tasks (
    id                TEXT PRIMARY KEY,
    level_id          TEXT NOT NULL REFERENCES public.course_levels(id) ON DELETE CASCADE,
    lesson_id         TEXT REFERENCES public.course_lessons(id) ON DELETE SET NULL,
    sort_order        INTEGER NOT NULL,
    title             TEXT NOT NULL,
    task_type         TEXT NOT NULL,                  -- code, sql, quiz
    kind              TEXT NOT NULL DEFAULT 'practice', -- practice, assessment, final
    prompt            TEXT NOT NULL,
    starter_code      TEXT,
    solution_code     TEXT,                           -- never sent to clients
    test_cases        TEXT,                           -- JSON [{stdin, expected_output, hidden}]
    setup_sql         TEXT,
    reference_sql     TEXT,                           -- never sent to clients
    check_sql         TEXT,                           -- for INSERT/UPDATE/DDL tasks
    order_matters     BOOLEAN DEFAULT FALSE,
    questions         TEXT,                           -- JSON quiz questions incl. answers (never sent)
    pass_mark         INTEGER DEFAULT 70,
    hints             TEXT,                           -- JSON list, progressive
    concept           TEXT NOT NULL,
    difficulty        TEXT NOT NULL DEFAULT 'Beginner',
    estimated_minutes INTEGER DEFAULT 20,
    xp_reward         INTEGER DEFAULT 25
);

-- 16. course_completions: one row per completed lesson / task / level / course.
--     The UNIQUE constraint is what makes XP and badges impossible to award twice.
CREATE TABLE IF NOT EXISTS public.course_completions (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    course_id    TEXT NOT NULL REFERENCES public.courses(id) ON DELETE CASCADE,
    item_type    TEXT NOT NULL,                       -- lesson, task, level, course
    item_id      TEXT NOT NULL,
    score        DOUBLE PRECISION,
    xp_awarded   INTEGER DEFAULT 0,
    completed_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, item_type, item_id)
);

-- 17. practice_attempts: every graded attempt with a real timestamp
--     (challenges and course tasks). Feeds learning-strain scoring.
CREATE TABLE IF NOT EXISTS public.practice_attempts (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    context_type      TEXT NOT NULL,                  -- challenge, course_task
    context_id        TEXT NOT NULL,
    passed            BOOLEAN NOT NULL,
    concept           TEXT,
    mistake_signature TEXT,
    execution_seconds DOUBLE PRECISION DEFAULT 0,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- 18. mistake_patterns: one row per (student, kind of mistake)
CREATE TABLE IF NOT EXISTS public.mistake_patterns (
    id               TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    signature        TEXT NOT NULL,                   -- e.g. c:loop-boundary
    category         TEXT NOT NULL,
    concept          TEXT NOT NULL,
    language         TEXT NOT NULL,
    occurrences      INTEGER DEFAULT 1,
    resolved_count   INTEGER DEFAULT 0,
    last_explanation TEXT,
    last_correction  TEXT,
    first_seen       TIMESTAMPTZ DEFAULT now(),
    last_seen        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, signature)
);

-- 19. mistake_occurrences: each individual time the mistake happened
CREATE TABLE IF NOT EXISTS public.mistake_occurrences (
    id                   TEXT PRIMARY KEY,
    pattern_id           TEXT NOT NULL REFERENCES public.mistake_patterns(id) ON DELETE CASCADE,
    user_id              TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    context_type         TEXT NOT NULL,               -- challenge, course_task, autopsy
    context_id           TEXT,
    context_title        TEXT,
    code_snippet         TEXT,
    error_excerpt        TEXT,
    explanation          TEXT,
    suggested_correction TEXT,
    fixed_code_snippet   TEXT,                        -- the student's own passing code, once fixed
    resolved_at          TIMESTAMPTZ,
    created_at           TIMESTAMPTZ DEFAULT now()
);

-- 20. hint_history
CREATE TABLE IF NOT EXISTS public.hint_history (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    context_type TEXT NOT NULL,
    context_id   TEXT NOT NULL,
    hint_level   INTEGER NOT NULL,                    -- 1 conceptual, 2 directional, 3 guided
    hint_text    TEXT NOT NULL,
    source       TEXT NOT NULL,                       -- llm, authored, rules
    strain_score INTEGER DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- 21. assistance_prompts: the student's response to a hint offer (prevents nagging)
CREATE TABLE IF NOT EXISTS public.assistance_prompts (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    context_type TEXT NOT NULL,
    context_id   TEXT NOT NULL,
    strain_score INTEGER DEFAULT 0,
    response     TEXT NOT NULL,                       -- accepted, dismissed
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- 22. learning_roadmaps
CREATE TABLE IF NOT EXISTS public.learning_roadmaps (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    track             TEXT NOT NULL,                  -- c, sql, mixed
    status            TEXT NOT NULL DEFAULT 'active', -- active, archived
    focus_summary     TEXT,
    priority_concepts TEXT,                           -- JSON list
    generated_with    TEXT DEFAULT 'rules',           -- rules, rules+llm
    start_date        DATE DEFAULT CURRENT_DATE,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- 23. roadmap_days
CREATE TABLE IF NOT EXISTS public.roadmap_days (
    id                TEXT PRIMARY KEY,
    roadmap_id        TEXT NOT NULL REFERENCES public.learning_roadmaps(id) ON DELETE CASCADE,
    day_number        INTEGER NOT NULL,
    day_type          TEXT NOT NULL,                  -- lesson, assessment, review, challenge
    topic             TEXT NOT NULL,
    objective         TEXT NOT NULL,
    explanation       TEXT NOT NULL,
    task_description  TEXT NOT NULL,
    difficulty        TEXT NOT NULL,
    estimated_minutes INTEGER DEFAULT 30,
    xp_reward         INTEGER DEFAULT 20,
    reason            TEXT,
    coach_tip         TEXT,
    course_id         TEXT,
    lesson_id         TEXT,
    linked_type       TEXT NOT NULL,                  -- course_task, challenge
    linked_id         TEXT NOT NULL,
    completed_at      TIMESTAMPTZ,
    UNIQUE (roadmap_id, day_number)
);

DO $$ BEGIN IF to_regclass('public.idx_levels_course') IS NULL THEN CREATE INDEX idx_levels_course ON public.course_levels(course_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_lessons_level') IS NULL THEN CREATE INDEX idx_lessons_level ON public.course_lessons(level_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_tasks_level') IS NULL THEN CREATE INDEX idx_tasks_level ON public.course_tasks(level_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_completions_user') IS NULL THEN CREATE INDEX idx_completions_user ON public.course_completions(user_id, course_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_attempts_user_time') IS NULL THEN CREATE INDEX idx_attempts_user_time ON public.practice_attempts(user_id, created_at); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_attempts_context') IS NULL THEN CREATE INDEX idx_attempts_context ON public.practice_attempts(user_id, context_type, context_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_mistake_patterns_user') IS NULL THEN CREATE INDEX idx_mistake_patterns_user ON public.mistake_patterns(user_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_mistake_occ_pattern') IS NULL THEN CREATE INDEX idx_mistake_occ_pattern ON public.mistake_occurrences(pattern_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_mistake_occ_context') IS NULL THEN CREATE INDEX idx_mistake_occ_context ON public.mistake_occurrences(user_id, context_type, context_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_hints_context') IS NULL THEN CREATE INDEX idx_hints_context ON public.hint_history(user_id, context_type, context_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_assist_context') IS NULL THEN CREATE INDEX idx_assist_context ON public.assistance_prompts(user_id, context_type, context_id); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_roadmaps_user') IS NULL THEN CREATE INDEX idx_roadmaps_user ON public.learning_roadmaps(user_id, status); END IF; END $$;
DO $$ BEGIN IF to_regclass('public.uq_roadmap_active') IS NULL THEN CREATE UNIQUE INDEX uq_roadmap_active ON public.learning_roadmaps(user_id) WHERE status = 'active'; END IF; END $$;
DO $$ BEGIN IF to_regclass('public.idx_roadmap_days_roadmap') IS NULL THEN CREATE INDEX idx_roadmap_days_roadmap ON public.roadmap_days(roadmap_id); END IF; END $$;

-- Row Level Security on every table: enabled only where it is not enabled yet
-- (ALTER TABLE takes an exclusive lock, so it must not run on every startup).
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['users', 'student_profiles', 'coding_challenges', 'code_submissions', 'execution_results', 'ai_feedback', 'learning_assessments', 'student_skills', 'learning_history', 'achievements', 'student_achievements', 'courses', 'course_levels', 'course_lessons', 'course_tasks', 'course_completions', 'practice_attempts', 'mistake_patterns', 'mistake_occurrences', 'hint_history', 'assistance_prompts', 'learning_roadmaps', 'roadmap_days'] LOOP
    IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = ('public.' || t)::regclass) THEN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END IF;
  END LOOP;
END $$;
