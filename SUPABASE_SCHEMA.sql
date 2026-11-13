-- =====================================================================
-- AI CODING MENTOR – SUPABASE (POSTGRESQL) PRODUCTION SCHEMA
-- Run this script in: Supabase Dashboard -> SQL Editor -> New Query -> Run
-- It creates all 11 tables, indexes, constraints, and seeds initial data.
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
    mastery_level      DOUBLE PRECISION DEFAULT 10.0,
    problems_solved    INTEGER DEFAULT 0,
    problems_attempted INTEGER DEFAULT 0,
    error_count        INTEGER DEFAULT 0,
    last_practiced     TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_student_skills_user_skill UNIQUE (user_id, skill_name)
);

-- 9. learning_history
CREATE TABLE IF NOT EXISTS public.learning_history (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
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
    CONSTRAINT uq_student_achievements_user_ach UNIQUE (user_id, achievement_id)
);

-- Indexes for high-performance querying
CREATE INDEX IF NOT EXISTS idx_submissions_user ON public.code_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_challenge ON public.code_submissions(challenge_id);
CREATE INDEX IF NOT EXISTS idx_skills_user ON public.student_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_history_user ON public.learning_history(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON public.ai_feedback(user_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coding_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.execution_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_achievements ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- INITIAL SEED DATA
-- =====================================================================

-- Seed Achievements
INSERT INTO public.achievements (id, code, title, description, badge_icon, xp_reward, milestone_threshold)
VALUES
    ('ach_first_code', 'FIRST_BLOOD', 'First Code Executed', 'Run your first program in the playground', 'Play', 50, 1),
    ('ach_first_solve', 'FIRST_SOLVE', 'Bug Hunter', 'Successfully pass all test cases for a challenge', 'Award', 100, 1),
    ('ach_autopsy', 'FORENSIC_CODER', 'Code Autopsy', 'Run an AI autopsy to diagnose a conceptual mistake', 'Search', 75, 1),
    ('ach_visual_trace', 'X_RAY_VISION', 'Visual Explorer', 'Step through code execution in the Visual Debugger', 'Eye', 75, 1),
    ('ach_three_streak', 'CONSISTENT_THINKER', '3-Day Streak', 'Practice coding 3 days in a row', 'Flame', 150, 3),
    ('ach_loops_master', 'LOOP_MASTER', 'Master of Loops', 'Solve 5 challenges on loops and iterations', 'Repeat', 200, 5)
ON CONFLICT (id) DO NOTHING;

-- Seed Challenges
INSERT INTO public.coding_challenges (id, title, slug, topic, difficulty, description, initial_code, solution_code, test_cases, constraints, hints, xp_reward)
VALUES
    (
        'ch_sum_list',
        'Sum of List Elements',
        'sum-of-list',
        'Loops & Lists',
        'Beginner',
        'Write a function `sum_numbers(numbers)` that takes a list of integers and returns their total sum. If the list is empty, return 0.',
        'def sum_numbers(numbers):\n    # Write your solution here\n    pass\n',
        'def sum_numbers(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total\n',
        '[{"input": "[1, 2, 3, 4, 5]", "expected_output": "15", "hidden": false}, {"input": "[-2, 5, 10]", "expected_output": "13", "hidden": false}, {"input": "[]", "expected_output": "0", "hidden": true}, {"input": "[100]", "expected_output": "100", "hidden": true}]',
        'Input is a list of integers. Length between 0 and 1000.',
        '["Consider initializing an accumulator variable like total = 0 before the loop.", "Loop through each item directly using for num in numbers:, not just the index.", "Make sure to return the accumulated total after the loop finishes, not inside it."]',
        50
    ),
    (
        'ch_find_max',
        'Find Maximum Number',
        'find-maximum-number',
        'Conditions',
        'Beginner',
        'Write a function `find_max(numbers)` that finds and returns the largest number in a non-empty list of integers without using the built-in `max()` function.',
        'def find_max(numbers):\n    # Do not use Python built-in max()\n    pass\n',
        'def find_max(numbers):\n    highest = numbers[0]\n    for n in numbers:\n        if n > highest:\n            highest = n\n    return highest\n',
        '[{"input": "[3, 7, 2, 9, 4]", "expected_output": "9", "hidden": false}, {"input": "[-10, -5, -20]", "expected_output": "-5", "hidden": false}, {"input": "[42]", "expected_output": "42", "hidden": true}]',
        'List will contain at least one integer. Values can be negative.',
        '["Initialize your maximum tracker to the first element numbers[0] instead of 0.", "Compare each number against your tracker using an if statement.", "Update the tracker only when the current element is greater."]',
        60
    ),
    (
        'ch_reverse_string',
        'Reverse a String',
        'reverse-string',
        'Strings',
        'Beginner',
        'Write a function `reverse_string(text)` that returns the reversed version of the given string.',
        'def reverse_string(text):\n    # Write your solution here\n    pass\n',
        'def reverse_string(text):\n    return text[::-1]\n',
        '[{"input": "\x27hello\x27", "expected_output": "\x27olleh\x27", "hidden": false}, {"input": "\x27Python\x27", "expected_output": "\x27nohtyP\x27", "hidden": false}, {"input": "\x27\x27", "expected_output": "\x27\x27", "hidden": true}]',
        'Input is a standard string. May contain spaces and punctuation.',
        '["In Python, strings can be reversed using extended slicing or a backwards loop.", "Check slice syntax string[::-1] or building a new string prepending characters."]',
        40
    ),
    (
        'ch_count_vowels',
        'Count Vowels in String',
        'count-vowels',
        'Strings & Conditions',
        'Beginner',
        'Write a function `count_vowels(s)` that counts how many vowels (a, e, i, o, u) exist in a string, case-insensitively.',
        'def count_vowels(s):\n    # Count both lowercase and uppercase vowels\n    pass\n',
        'def count_vowels(s):\n    vowels = set(\x27aeiouAEIOU\x27)\n    return sum(1 for char in s if char in vowels)\n',
        '[{"input": "\x27Algorithm\x27", "expected_output": "3", "hidden": false}, {"input": "\x27sky\x27", "expected_output": "0", "hidden": false}, {"input": "\x27AEIOU\x27", "expected_output": "5", "hidden": true}]',
        'String length 0 to 500.',
        '["Convert the input to lowercase or check against both lowercase and uppercase vowels.", "Use the in keyword to test if a character is in a vowel string/set like \x27aeiou\x27."]',
        50
    ),
    (
        'ch_fibonacci',
        'Nth Fibonacci Number',
        'nth-fibonacci',
        'Recursion & Functions',
        'Intermediate',
        'Write a function `fibonacci(n)` that returns the nth Fibonacci number, where F(0) = 0 and F(1) = 1.',
        'def fibonacci(n):\n    # Return the nth Fibonacci number\n    pass\n',
        'def fibonacci(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n',
        '[{"input": "0", "expected_output": "0", "hidden": false}, {"input": "1", "expected_output": "1", "hidden": false}, {"input": "6", "expected_output": "8", "hidden": false}, {"input": "10", "expected_output": "55", "hidden": true}]',
        '0 <= n <= 30',
        '["Identify your base cases: what should happen when n is 0 or 1?", "An iterative loop using two variables a, b is O(N) time and avoids recursion stack depth limits."]',
        80
    )
ON CONFLICT (id) DO NOTHING;
