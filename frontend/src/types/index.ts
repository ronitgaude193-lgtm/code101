export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export interface StudentProfile {
  user_id: string;
  full_name: string;
  email: string;
  current_level: number;
  total_xp: number;
  streak_days: number;
  last_active_date?: string;
  preferred_language: string;
  bio: string;
}

export interface TestCase {
  input: string;
  expected_output: string;
  hidden: boolean;
}

export interface ChallengeSummary {
  id: string;
  title: string;
  slug: string;
  topic: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  description: string;
  xp_reward: number;
  solved: boolean;
  visibility?: "public" | "private";
  is_mine?: boolean;
}

export interface ChallengeDetail extends ChallengeSummary {
  initial_code: string;
  solution_code?: string;
  test_cases: TestCase[];
  constraints?: string;
  hints: string[];
}

export interface CodeRunResult {
  stdout: string;
  stderr: string;
  compile_output?: string;
  exit_code: number;
  execution_time: number;
  status: string;
}

export interface TestResultDetail {
  case_index: number;
  input: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  hidden: boolean;
}

export interface CodeSubmitResult {
  submission_id: string;
  status: string;
  all_passed: boolean;
  passed_count: number;
  total_count: number;
  test_results: TestResultDetail[];
  xp_earned: number;
  new_total_xp: number;
  new_level: number;
  new_streak: number;
  unlocked_achievements: string[];
  execution_seconds?: number;
  deja_vu?: DejaVu | null;
  assistance?: StrainAssessment | null;
}

export interface TraceStep {
  step: number;
  line: number;
  event: "line" | "call" | "return" | "exception";
  func_name: string;
  variables: Record<string, any>;
  stdout_so_far: string;
  stack: string[];
}

export interface VisualTraceResult {
  success: boolean;
  steps: TraceStep[];
  total_steps: number;
  error?: string;
  output: string;
}

export interface AIMentorResult {
  mode: "learning" | "debugging" | "hint";
  summary: string;
  explanation: string;
  hints: string[];
  suggested_fix?: string;
  conceptual_takeaway: string;
  related_topics: string[];
  is_simulated: boolean;
}

export interface LoopIterationAnalysis {
  iteration: number;
  variable_states: Record<string, any>;
  what_happened: string;
  expected_state?: string;
}

export interface AutopsyResult {
  primary_failure_reason: string;
  syntax_vs_logic: string;
  misconception_identified: string;
  detailed_walkthrough: string;
  loop_timeline?: LoopIterationAnalysis[];
  guiding_hint: string;
  practice_prompt: string;
  is_simulated: boolean;
}

export interface SkillProgress {
  skill_name: string;
  mastery_level: number;
  problems_solved: number;
  problems_attempted: number;
  error_count: number;
  status: "Strong" | "Developing" | "Needs Focus";
}

export interface WeaknessItem {
  topic: string;
  error_rate: number;
  recommendation: string;
  recommended_challenge_id?: string;
}

export interface ProgrammingDNAResult {
  logical_thinking_score: number;
  debugging_skill_score: number;
  code_correctness_score: number;
  problem_solving_speed: number;
  hint_independence_score: number;
  consistency_score: number;
  top_strengths: string[];
  key_growth_areas: string[];
  overall_dna_archetype: string;
}

export interface DashboardData {
  profile: StudentProfile;
  problems_attempted: number;
  problems_solved: number;
  solve_rate: number;
  skills: SkillProgress[];
  weaknesses: WeaknessItem[];
  recent_activity: Array<{
    event_type: string;
    details: any;
    xp_earned: number;
    created_at: string;
  }>;
  programming_dna: ProgrammingDNAResult;
  recommended_challenges: ChallengeSummary[];
}

export interface Achievement {
  id: string;
  code: string;
  title: string;
  description: string;
  badge_icon: string;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
  category?: "general" | "course";
  course_title?: string | null;
}

// ---------------------------------------------------------------------------
// Learning extensions: Mistake Memory, Learning-Strain Assistance, Academy, Roadmap
// ---------------------------------------------------------------------------
export type ContextType = "challenge" | "course_task";

export interface MistakeOccurrence {
  occurrence_id: string;
  context_type: string;
  context_id?: string;
  context_title?: string;
  code_snippet?: string;
  error_excerpt?: string;
  explanation?: string;
  suggested_correction?: string;
  fixed_code_snippet?: string | null;
  resolved: boolean;
  created_at?: string;
  when: string;
  category?: string;
  concept?: string;
}

export interface DejaVu {
  status: "repeat" | "related" | "first_time";
  current: {
    category: string;
    concept: string;
    signature: string;
    explanation: string;
    suggested_correction: string;
  };
  previous: MistakeOccurrence | null;
  related_concept: string;
  recommendation: string;
  occurrence_id: string;
  pattern_id: string;
  occurrences: number;
}

export interface StrainSignal {
  signal: string;
  points: number;
  detail: string;
}

export interface RecoverySuggestion {
  type: "break" | "review" | "easier_problem";
  title: string;
  detail: string;
  target_type: "course_lesson" | "course_task" | "challenge" | null;
  target_id: string | null;
}

export interface StrainAssessment {
  context_type: ContextType;
  context_id: string;
  strain_score: number;
  level: "low" | "moderate" | "high";
  signals: StrainSignal[];
  consecutive_failures: number;
  session_minutes: number;
  hints_used: number;
  next_hint_level: number | null;
  offer_hint: boolean;
  message: string | null;
  recovery: RecoverySuggestion[];
  recommended_difficulty: "easier" | "normal";
  disclaimer: string;
}

export interface HintResult {
  level: number | null;
  level_name: string | null;
  hint: string | null;
  source: "llm" | "authored" | "rules" | null;
  exhausted: boolean;
  hints_remaining: number;
  recovery: RecoverySuggestion[];
}

export interface MistakePattern {
  pattern_id: string;
  signature: string;
  category: string;
  concept: string;
  language: string;
  occurrences: number;
  resolved_count: number;
  is_repeated: boolean;
  explanation?: string;
  suggested_correction?: string;
  first_seen?: string;
  last_seen?: string;
  recent_occurrences: MistakeOccurrence[];
}

export interface MemoryPatternsResult {
  patterns: MistakePattern[];
  total_mistakes: number;
  repeated_patterns: number;
}

export interface ReplayFeedback {
  summary: string;
  explanation: string;
  hints?: string[];
  what_to_do_differently?: string;
  source: "llm" | "rules";
}

export interface MemoryReplayResult {
  current_mistake: {
    occurrence_id: string;
    category: string;
    concept: string;
    language: string;
    context_title?: string;
    code_snippet?: string;
    error_excerpt?: string;
  };
  generic: ReplayFeedback;
  personalized: ReplayFeedback | null;
  first_time: boolean;
  first_time_message: string | null;
  memory_used: Array<{
    relation: "repeat" | "related";
    category: string;
    context_title?: string;
    when: string;
    resolved: boolean;
    suggested_correction?: string;
    fixed_code_snippet?: string | null;
  }>;
}

export interface CourseProgress {
  completed_items: number;
  total_items: number;
  percent: number;
  levels_completed: number;
  total_levels: number;
}

export interface CourseSummary {
  id: string;
  slug: string;
  title: string;
  description: string;
  language: "c" | "sql";
  icon: string;
  completion_xp: number;
  badge_title?: string;
  badge_icon?: string;
  level_titles: string[];
  lesson_count: number;
  task_count: number;
  progress: CourseProgress;
  completed: boolean;
  current_level: number | null;
}

export interface CourseTaskBrief {
  id: string;
  title: string;
  task_type: "code" | "sql" | "quiz";
  kind: "practice" | "assessment" | "final";
  concept: string;
  difficulty: string;
  estimated_minutes: number;
  xp_reward: number;
  pass_mark: number;
  completed: boolean;
  unlocked?: boolean;
  best_score?: number | null;
}

export interface CourseLessonBrief {
  id: string;
  title: string;
  summary: string;
  concept: string;
  estimated_minutes: number;
  xp_reward: number;
  completed: boolean;
  task: CourseTaskBrief | null;
}

export interface CourseLevel {
  id: string;
  level_number: number;
  title: string;
  description: string;
  unlocked: boolean;
  completed: boolean;
  lessons: CourseLessonBrief[];
  assessment: CourseTaskBrief | null;
}

export interface CourseDetail {
  id: string;
  slug: string;
  title: string;
  description: string;
  language: "c" | "sql";
  icon: string;
  completion_xp: number;
  badge_title?: string;
  badge_icon?: string;
  completed: boolean;
  progress: CourseProgress;
  levels: CourseLevel[];
}

export interface LessonDetail {
  id: string;
  title: string;
  summary: string;
  content: string;
  concept: string;
  estimated_minutes: number;
  xp_reward: number;
  level_number: number;
  level_title: string;
  course_slug: string;
  course_title: string;
  unlocked: boolean;
  completed: boolean;
  task: CourseTaskBrief | null;
}

export interface QuizQuestion {
  index: number;
  question: string;
  options: string[];
  concept?: string;
}

export interface CourseTaskDetail extends CourseTaskBrief {
  prompt: string;
  starter_code: string;
  order_matters: boolean;
  is_modification_task: boolean;
  visible_tests: Array<{ stdin: string; expected_output: string }>;
  hidden_test_count: number;
  questions: QuizQuestion[];
  course_slug: string;
  course_title: string;
  course_language: "c" | "sql";
  level_number: number;
  level_title: string;
  lesson_id: string | null;
  lesson_title: string | null;
  lock_reason: string | null;
  attempts: number;
  hints_used: number;
  hints_available: boolean;
}

export interface SqlRunResult {
  kind: "sql";
  ok: boolean;
  columns?: string[];
  rows?: any[][];
  truncated?: boolean;
  error?: string;
  stage?: string;
}

export interface CodeRunTaskResult extends CodeRunResult {
  kind: "code";
  success: boolean;
}

export interface QuizFeedback {
  index: number;
  correct: boolean;
  chosen: number | null;
  correct_option?: number;
  explanation: string;
  concept: string;
}

export interface CourseSubmitResult {
  passed: boolean;
  status: string;
  passed_count: number;
  total_count: number;
  test_results: TestResultDetail[];
  error: string | null;
  score?: number;
  details: any;
  recorded: boolean;
  xp_earned: number;
  already_completed?: boolean;
  level_completed?: boolean;
  course_completed?: boolean;
  badge_awarded?: {
    id: string;
    title: string;
    description: string;
    badge_icon: string;
    course_title: string;
    unlocked_at: string;
  } | null;
  new_total_xp?: number;
  new_level?: number;
  deja_vu?: DejaVu | null;
  assistance?: StrainAssessment | null;
  roadmap_days_completed?: Array<{ day_number: number; topic: string; xp_earned: number }>;
}

export interface RoadmapDay {
  id: string;
  day_number: number;
  day_type: "lesson" | "assessment" | "review" | "challenge";
  topic: string;
  objective: string;
  explanation: string;
  task_description: string;
  difficulty: string;
  estimated_minutes: number;
  xp_reward: number;
  reason?: string;
  coach_tip?: string | null;
  course_slug?: string | null;
  course_title?: string | null;
  lesson_id?: string | null;
  linked_type: "course_task" | "challenge";
  linked_id: string;
  completed: boolean;
  completed_at?: string | null;
  scheduled_date: string;
}

export interface Roadmap {
  id: string;
  track: "c" | "sql" | "mixed";
  focus_summary: string;
  priority_concepts: Array<{ concept: string; score: number; evidence: string }>;
  generated_with: "rules" | "rules+llm";
  start_date: string;
  created_at: string;
  days: RoadmapDay[];
  total_days: number;
  completed_days: number;
  percent: number;
  current_day: RoadmapDay | null;
  xp_earned: number;
}
