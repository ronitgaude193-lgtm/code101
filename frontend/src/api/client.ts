import {
  StudentProfile,
  ChallengeSummary,
  ChallengeDetail,
  CodeRunResult,
  CodeSubmitResult,
  VisualTraceResult,
  AIMentorResult,
  AutopsyResult,
  DashboardData,
  Achievement,
  ContextType,
  StrainAssessment,
  HintResult,
  MemoryPatternsResult,
  MemoryReplayResult,
  CourseSummary,
  CourseDetail,
  LessonDetail,
  CourseTaskDetail,
  CourseSubmitResult,
  SqlRunResult,
  CodeRunTaskResult,
  Roadmap
} from "../types";

// Same-origin when FastAPI serves the built app; the dev server (Vite) talks to the backend directly.
const API_BASE = import.meta.env.DEV ? "http://localhost:8000/api" : "/api";

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("mentor_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorMsg = `Server error (${res.status})`;
      try {
        const errorData = await res.json();
        errorMsg = errorData.detail || errorMsg;
      } catch {
        // fallback
      }
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err: any) {
    if (err.message?.includes("Failed to fetch") || err.message?.includes("NetworkError")) {
      throw new Error("Cannot connect to backend server. Please verify backend is running on port 8000.");
    }
    throw err;
  }
}

export const api = {
  // Auth
  register: (data: { email: string; password: string; full_name: string; preferred_language?: string }) =>
    request<{ access_token: string; user: any }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getProfile: () => request<StudentProfile>("/auth/me"),

  updateProfile: (data: { full_name?: string; preferred_language?: string; bio?: string }) =>
    request<StudentProfile>("/auth/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Challenges
  getChallenges: (topic?: string, difficulty?: string) => {
    const params = new URLSearchParams();
    if (topic) params.append("topic", topic);
    if (difficulty) params.append("difficulty", difficulty);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return request<ChallengeSummary[]>(`/challenges${qs}`);
  },

  getChallenge: (idOrSlug: string) => request<ChallengeDetail>(`/challenges/${idOrSlug}`),

  generateChallenge: (topic: string, difficulty: string, visibility: "private" | "public" = "private") =>
    request<ChallengeDetail>(`/challenges/generate?topic=${encodeURIComponent(topic)}&difficulty=${encodeURIComponent(difficulty)}&visibility=${visibility}`, {
      method: "POST",
    }),

  // Execution
  runCode: (code: string, language: string = "python", stdin: string = "") =>
    request<CodeRunResult>("/execution/run", {
      method: "POST",
      body: JSON.stringify({ code, language, stdin }),
    }),

  submitCode: (challengeId: string, code: string, language: string = "python") =>
    request<CodeSubmitResult>("/execution/submit", {
      method: "POST",
      body: JSON.stringify({ challenge_id: challengeId, code, language }),
    }),

  traceCode: (code: string, stdin: string = "", maxSteps: number = 150) =>
    request<VisualTraceResult>("/execution/trace", {
      method: "POST",
      body: JSON.stringify({ code, stdin, max_steps: maxSteps }),
    }),

  // AI Mentor & Autopsy
  askMentor: (payload: {
    code: string;
    language?: string;
    mode: "learning" | "debugging" | "hint";
    prompt?: string;
    challenge_id?: string;
    execution_output?: string;
    error_message?: string;
  }) =>
    request<AIMentorResult>("/ai/mentor", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  runAutopsy: (payload: {
    code: string;
    language?: string;
    challenge_id?: string;
    expected_behavior?: string;
    actual_output?: string;
    error_message?: string;
  }) =>
    request<AutopsyResult>("/ai/autopsy", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Analytics & Gamification
  getDashboard: () => request<DashboardData>("/analytics/dashboard"),

  getAchievements: () => request<Achievement[]>("/achievements"),

  getHealth: () => request<any>("/health"),

  // Coding Academy
  getCourses: () => request<CourseSummary[]>("/academy/courses"),
  getCourse: (slug: string) => request<CourseDetail>(`/academy/courses/${encodeURIComponent(slug)}`),
  getLesson: (id: string) => request<LessonDetail>(`/academy/lessons/${encodeURIComponent(id)}`),
  completeLesson: (id: string) =>
    request<{ xp_earned: number; newly_completed: boolean; roadmap_days_completed: any[] }>(
      `/academy/lessons/${encodeURIComponent(id)}/complete`, { method: "POST" }),
  getCourseTask: (id: string) => request<CourseTaskDetail>(`/academy/tasks/${encodeURIComponent(id)}`),
  runCourseTask: (id: string, code: string, stdin: string = "") =>
    request<SqlRunResult | CodeRunTaskResult>(`/academy/tasks/${encodeURIComponent(id)}/run`, {
      method: "POST",
      body: JSON.stringify({ code, stdin }),
    }),
  submitCourseTask: (id: string, payload: { code?: string; answers?: number[] }) =>
    request<CourseSubmitResult>(`/academy/tasks/${encodeURIComponent(id)}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Personalized Roadmap
  getRoadmap: () => request<{ roadmap: Roadmap | null }>("/roadmap"),
  generateRoadmap: (track: "c" | "sql" | "mixed") =>
    request<{ roadmap: Roadmap }>("/roadmap/generate", { method: "POST", body: JSON.stringify({ track }) }),
  completeRoadmapDay: (dayId: string) =>
    request<{ completed: boolean; already_completed: boolean; xp_earned: number; message: string }>(
      `/roadmap/days/${encodeURIComponent(dayId)}/complete`, { method: "POST" }),

  // Mistake Memory & Memory Replay
  getMistakePatterns: () => request<MemoryPatternsResult>("/memory/patterns"),
  memoryReplay: (occurrenceId: string) =>
    request<MemoryReplayResult>("/memory/replay", { method: "POST", body: JSON.stringify({ occurrence_id: occurrenceId }) }),

  // Learning-strain assistance & progressive hints
  getStrain: (contextType: ContextType, contextId: string) =>
    request<StrainAssessment>(`/assist/strain?context_type=${contextType}&context_id=${encodeURIComponent(contextId)}`),
  respondToHintOffer: (contextType: ContextType, contextId: string, accepted: boolean) =>
    request<{ recorded: boolean }>("/assist/respond", {
      method: "POST",
      body: JSON.stringify({ context_type: contextType, context_id: contextId, accepted }),
    }),
  getNextHint: (contextType: ContextType, contextId: string, code?: string) =>
    request<HintResult>("/assist/hint", {
      method: "POST",
      body: JSON.stringify({ context_type: contextType, context_id: contextId, code }),
    }),
};
