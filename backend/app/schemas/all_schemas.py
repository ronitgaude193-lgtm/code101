from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# Authentication & Users
class UserRegister(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    preferred_language: Optional[str] = "python"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class StudentProfileResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    current_level: int
    total_xp: int
    streak_days: int
    last_active_date: Optional[str]
    preferred_language: str
    bio: str

class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    bio: Optional[str] = None

# Challenges
class TestCase(BaseModel):
    input: str
    expected_output: str
    hidden: bool = False

class ChallengeSummary(BaseModel):
    id: str
    title: str
    slug: str
    topic: str
    difficulty: str
    description: str
    xp_reward: int
    solved: bool = False
    visibility: str = "public"   # public, private
    is_mine: bool = False

class ChallengeDetail(BaseModel):
    id: str
    title: str
    slug: str
    topic: str
    difficulty: str
    description: str
    initial_code: str
    solution_code: Optional[str] = None
    test_cases: List[TestCase]
    constraints: Optional[str] = None
    hints: List[str]
    xp_reward: int
    solved: bool = False
    visibility: str = "public"   # public, private
    is_mine: bool = False

class ChallengeCreate(BaseModel):
    title: str
    topic: str
    difficulty: str
    description: str
    initial_code: str
    solution_code: Optional[str] = None
    test_cases: List[TestCase]
    constraints: Optional[str] = None
    hints: List[str] = []
    xp_reward: int = 50

# Execution & Submissions
class CodeRunRequest(BaseModel):
    code: str
    language: str = "python"
    stdin: Optional[str] = ""

class CodeRunResponse(BaseModel):
    stdout: str
    stderr: str
    compile_output: Optional[str] = None
    exit_code: int
    execution_time: float
    status: str  # Success, Error, Timeout, Blocked

class CodeSubmitRequest(BaseModel):
    challenge_id: str
    code: str
    language: str = "python"

class TestResultDetail(BaseModel):
    case_index: int
    input: str
    expected_output: str
    actual_output: str
    passed: bool
    hidden: bool

class CodeSubmitResponse(BaseModel):
    submission_id: str
    status: str # Accepted, Wrong Answer, Runtime Error, Syntax Error, Timeout
    all_passed: bool
    passed_count: int
    total_count: int
    test_results: List[TestResultDetail]
    xp_earned: int
    new_total_xp: int
    new_level: int
    new_streak: int
    unlocked_achievements: List[str]
    # Learning extensions (optional, backward compatible)
    execution_seconds: float = 0.0
    deja_vu: Optional[Dict[str, Any]] = None
    assistance: Optional[Dict[str, Any]] = None

# Visual Execution Tracing
class TraceStep(BaseModel):
    step: int
    line: int
    event: str # line, call, return, exception
    func_name: str
    variables: Dict[str, Any]
    stdout_so_far: str
    stack: List[str]

class VisualTraceRequest(BaseModel):
    code: str
    stdin: Optional[str] = ""
    max_steps: int = 150

class VisualTraceResponse(BaseModel):
    success: bool
    steps: List[TraceStep]
    total_steps: int
    error: Optional[str] = None
    output: str

# AI Mentor & Autopsy
class AIMentorRequest(BaseModel):
    code: str
    language: str = "python"
    mode: str = "learning" # learning, debugging, hint
    prompt: Optional[str] = None
    challenge_id: Optional[str] = None
    execution_output: Optional[str] = None
    error_message: Optional[str] = None

class AIMentorResponse(BaseModel):
    mode: str
    summary: str
    explanation: str
    hints: List[str]
    suggested_fix: Optional[str] = None
    conceptual_takeaway: str
    related_topics: List[str]
    is_simulated: bool = False

class AutopsyRequest(BaseModel):
    code: str
    language: str = "python"
    challenge_id: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_output: Optional[str] = None
    error_message: Optional[str] = None

class LoopIterationAnalysis(BaseModel):
    iteration: int
    variable_states: Dict[str, Any]
    what_happened: str
    expected_state: Optional[str] = None

class AutopsyResponse(BaseModel):
    primary_failure_reason: str
    syntax_vs_logic: str
    misconception_identified: str
    detailed_walkthrough: str
    loop_timeline: Optional[List[LoopIterationAnalysis]] = None
    guiding_hint: str
    practice_prompt: str
    is_simulated: bool = False

# Adaptive Learning & Analytics
class SkillProgress(BaseModel):
    skill_name: str
    mastery_level: float
    problems_solved: int
    problems_attempted: int
    error_count: int
    status: str # Strong, Developing, Needs Focus

class WeaknessItem(BaseModel):
    topic: str
    error_rate: float
    recommendation: str
    recommended_challenge_id: Optional[str]

class ProgrammingDNAResponse(BaseModel):
    logical_thinking_score: int
    debugging_skill_score: int
    code_correctness_score: int
    problem_solving_speed: int
    hint_independence_score: int
    consistency_score: int
    top_strengths: List[str]
    key_growth_areas: List[str]
    overall_dna_archetype: str # e.g. "Algorithmic Architect", "Rapid Explorer", "Methodical Debugger"

class DashboardResponse(BaseModel):
    profile: StudentProfileResponse
    problems_attempted: int
    problems_solved: int
    solve_rate: float
    skills: List[SkillProgress]
    weaknesses: List[WeaknessItem]
    recent_activity: List[Dict[str, Any]]
    programming_dna: ProgrammingDNAResponse
    recommended_challenges: List[ChallengeSummary]

class AchievementResponse(BaseModel):
    id: str
    code: str
    title: str
    description: str
    badge_icon: str
    xp_reward: int
    unlocked: bool
    unlocked_at: Optional[str]
    category: str = "general"          # general, course
    course_title: Optional[str] = None


# ---------------------------------------------------------------------------
# Learning extensions: Coding Academy, Roadmap, Mistake Memory, Assistance
# ---------------------------------------------------------------------------


class CourseTaskRunRequest(BaseModel):
    code: str = Field(..., max_length=20000)
    stdin: Optional[str] = Field("", max_length=5000)


class CourseTaskSubmitRequest(BaseModel):
    code: Optional[str] = Field(None, max_length=20000)
    answers: Optional[List[int]] = Field(None, max_length=50)


class RoadmapGenerateRequest(BaseModel):
    track: Literal["c", "sql", "mixed"] = "mixed"


class AssistContext(BaseModel):
    context_type: Literal["challenge", "course_task"]
    context_id: str = Field(..., min_length=1, max_length=100)


class HintRequest(AssistContext):
    code: Optional[str] = Field(None, max_length=20000)


class AssistResponseRequest(AssistContext):
    accepted: bool


class MemoryReplayRequest(BaseModel):
    occurrence_id: str = Field(..., min_length=1, max_length=100)
