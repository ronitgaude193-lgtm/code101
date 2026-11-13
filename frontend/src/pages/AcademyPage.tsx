import React, { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import confetti from "canvas-confetti";
import {
  ArrowLeft, BookOpen, Check, CheckCircle, Lock, Play, Send, Cpu, Database, Award, Clock, Zap, FileQuestion,
  Code, AlertCircle, GraduationCap, ChevronRight,
} from "lucide-react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import {
  CourseSummary, CourseDetail, LessonDetail, CourseTaskDetail, CourseSubmitResult, SqlRunResult,
  CodeRunTaskResult, QuizFeedback,
} from "../types";
import { MarkdownLite } from "../components/MarkdownLite";
import { DejaVuPanel } from "../components/DejaVuPanel";
import { AssistancePanel } from "../components/AssistancePanel";
import { MemoryReplayView } from "../components/MemoryReplayView";

export type AcademyTarget =
  | { view: "courses" }
  | { view: "course"; slug: string }
  | { view: "lesson"; lessonId: string }
  | { view: "task"; taskId: string };

interface AcademyPageProps {
  target: AcademyTarget;
  onNavigate: (t: AcademyTarget) => void;
  onOpenAuth: () => void;
  onOpenChallenge: (id: string) => void;
}

const CourseIcon: React.FC<{ language: string; size?: number }> = ({ language, size = 22 }) =>
  language === "sql" ? <Database size={size} className="text-cyan-400" /> : <Cpu size={size} className="text-emerald-400" />;

const ProgressBar: React.FC<{ percent: number }> = ({ percent }) => (
  <div className="progress-track" aria-label={`${percent}% complete`}>
    <div className="progress-fill" style={{ width: `${Math.min(100, percent)}%` }} />
  </div>
);

export const AcademyPage: React.FC<AcademyPageProps> = ({ target, onNavigate, onOpenAuth, onOpenChallenge }) => {
  if (target.view === "course") return <CourseView slug={target.slug} onNavigate={onNavigate} />;
  if (target.view === "lesson") return <LessonView lessonId={target.lessonId} onNavigate={onNavigate} onOpenAuth={onOpenAuth} />;
  if (target.view === "task")
    return <TaskView taskId={target.taskId} onNavigate={onNavigate} onOpenAuth={onOpenAuth} onOpenChallenge={onOpenChallenge} />;
  return <CourseList onNavigate={onNavigate} />;
};

/* ----------------------------------------------------------- course list */
const CourseList: React.FC<{ onNavigate: (t: AcademyTarget) => void }> = ({ onNavigate }) => {
  const [courses, setCourses] = useState<CourseSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getCourses().then(setCourses).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h2><GraduationCap size={22} className="text-cyan-400" /> Coding Academy</h2>
          <p>Structured courses with levels, verified practice tasks, assessments and completion badges.</p>
        </div>
      </div>
      {error && <div className="inline-error">{error}</div>}
      {!courses && !error && <div className="page-loading"><div className="spinner"></div><p>Loading courses…</p></div>}
      <div className="course-grid">
        {courses?.map((c) => (
          <button key={c.id} className="course-card" onClick={() => onNavigate({ view: "course", slug: c.slug })}>
            <div className="course-card-top">
              <div className="course-icon"><CourseIcon language={c.language} size={26} /></div>
              {c.completed ? <span className="pill-ok"><Award size={12} /> Completed</span>
                : c.current_level ? <span className="pill-info">Level {c.current_level}</span> : null}
            </div>
            <h3>{c.title}</h3>
            <p className="course-desc">{c.description}</p>
            <div className="course-levels-row">
              {c.level_titles.map((t, i) => <span key={i} className="level-chip">L{i + 1} · {t}</span>)}
            </div>
            <div className="course-meta">
              <span><BookOpen size={13} /> {c.lesson_count} lessons</span>
              <span><Code size={13} /> {c.task_count} tasks</span>
              <span><Award size={13} /> {c.badge_title}</span>
            </div>
            <ProgressBar percent={c.progress.percent} />
            <span className="course-progress-label">
              {c.progress.percent}% · {c.progress.levels_completed}/{c.progress.total_levels} levels
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

/* ------------------------------------------------------------ course view */
const CourseView: React.FC<{ slug: string; onNavigate: (t: AcademyTarget) => void }> = ({ slug, onNavigate }) => {
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setCourse(null);
    api.getCourse(slug).then(setCourse).catch((e) => setError(e.message));
  }, [slug]);

  if (error) return <div className="page-shell"><div className="inline-error">{error}</div></div>;
  if (!course) return <div className="page-loading"><div className="spinner"></div><p>Loading course…</p></div>;

  // The one node that bounces "Start": the first open item not yet completed.
  const currentKey = course.levels
    .filter((lvl) => lvl.unlocked)
    .flatMap((lvl) => [
      ...lvl.lessons.flatMap((l) => [{ id: l.id, done: l.completed }, ...(l.task ? [{ id: l.task.id, done: l.task.completed }] : [])]),
      ...(lvl.assessment?.unlocked ? [{ id: lvl.assessment.id, done: lvl.assessment.completed }] : []),
    ])
    .find((x) => !x.done)?.id;

  return (
    <div className="page-shell">
      <button className="back-link" onClick={() => onNavigate({ view: "courses" })}><ArrowLeft size={15} /> All courses</button>
      <div className="course-hero">
        <div className="course-icon lg"><CourseIcon language={course.language} size={30} /></div>
        <div className="course-hero-text">
          <h2>{course.title}</h2>
          <p>{course.description}</p>
          <ProgressBar percent={course.progress.percent} />
          <span className="course-progress-label">
            {course.progress.completed_items}/{course.progress.total_items} items · {course.progress.levels_completed}/{course.progress.total_levels} levels
            {course.completed && <> · <Award size={12} /> {course.badge_title}</>}
          </span>
        </div>
      </div>

      <div className="path">
        {course.levels.map((lvl) => {
          // lesson -> its practice task -> ... -> level assessment, in course order
          const steps = lvl.lessons.flatMap((l) => [
            {
              key: l.id, kind: "lesson", done: l.completed, open: lvl.unlocked, icon: BookOpen, title: l.title,
              target: { view: "lesson", lessonId: l.id } as AcademyTarget,
              sub: <>{l.concept} · {l.estimated_minutes} min · <span className="xp-tag">+{l.xp_reward} XP</span></>,
            },
            ...(l.task ? [{
              key: l.task.id, kind: "task", done: l.task.completed, open: lvl.unlocked,
              icon: l.task.task_type === "quiz" ? FileQuestion : Code, title: l.task.title,
              target: { view: "task", taskId: l.task.id } as AcademyTarget,
              sub: <><span className={`diff-badge diff-${l.task.difficulty.toLowerCase()}`}>{l.task.difficulty}</span><span className="xp-tag">+{l.task.xp_reward} XP</span></>,
            }] : []),
          ]);
          const a = lvl.assessment;
          if (a) steps.push({
            key: a.id, kind: "assessment", done: a.completed, open: a.unlocked || a.completed, icon: Award, title: a.title,
            target: { view: "task", taskId: a.id },
            sub: <>
              {a.kind === "final" ? "Final course assessment" : "Level assessment"} · pass mark {a.pass_mark}% · <span className="xp-tag">+{a.xp_reward} XP</span>
              {a.best_score != null && ` · best ${a.best_score}%`}
              {!a.unlocked && !a.completed && " · complete this level's practice tasks to unlock"}
            </>,
          });
          return (
            <section key={lvl.id} className={`unit ${lvl.unlocked ? "" : "locked"} ${lvl.completed ? "done" : ""}`}>
              <header className="unit-banner">
                <div>
                  <h3>Level {lvl.level_number} · {lvl.title}</h3>
                  <p>{lvl.description}</p>
                </div>
                {lvl.completed ? <CheckCircle size={28} aria-label="Level completed" /> : !lvl.unlocked && <Lock size={24} aria-label="Locked" />}
              </header>
              {!lvl.unlocked && <p className="unit-lock-note">Pass the Level {lvl.level_number - 1} assessment to unlock.</p>}
              <ol className="path-steps">
                {steps.map((s, i) => {
                  const current = s.key === currentKey;
                  const Icon = s.done ? Check : s.open ? s.icon : Lock;
                  return (
                    <li key={s.key} style={{ "--i": i } as React.CSSProperties}>
                      <button
                        className={`step ${s.kind} ${s.done ? "done" : ""} ${s.open ? "" : "locked"} ${current ? "current" : ""}`}
                        disabled={!s.open}
                        onClick={() => onNavigate(s.target)}
                      >
                        {current && <span className="node-bubble"><span>Start</span></span>}
                        <span className="node"><Icon size={28} strokeWidth={3} /></span>
                        <span className="node-label">
                          <span className="lesson-title">{s.title}</span>
                          <span className="lesson-sub">{s.sub}</span>
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ol>
            </section>
          );
        })}
      </div>
    </div>
  );
};

/* ------------------------------------------------------------ lesson view */
const LessonView: React.FC<{ lessonId: string; onNavigate: (t: AcademyTarget) => void; onOpenAuth: () => void }> = ({ lessonId, onNavigate, onOpenAuth }) => {
  const { isAuthenticated, refreshProfile } = useAuth();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = () => api.getLesson(lessonId).then(setLesson).catch((e) => setError(e.message));
  useEffect(() => { setLesson(null); setNotice(null); load(); }, [lessonId]);

  const complete = async () => {
    if (!isAuthenticated) return onOpenAuth();
    try {
      const r = await api.completeLesson(lessonId);
      setNotice(r.xp_earned > 0 ? `Lesson complete: +${r.xp_earned} XP` : "Lesson already completed. XP is only awarded once.");
      await refreshProfile();
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (error) return <div className="page-shell"><div className="inline-error">{error}</div></div>;
  if (!lesson) return <div className="page-loading"><div className="spinner"></div><p>Loading lesson…</p></div>;

  return (
    <div className="page-shell narrow">
      <button className="back-link" onClick={() => onNavigate({ view: "course", slug: lesson.course_slug })}>
        <ArrowLeft size={15} /> {lesson.course_title} · Level {lesson.level_number}
      </button>
      <article className="lesson-article">
        <span className="eyebrow">{lesson.concept} · {lesson.estimated_minutes} min</span>
        <h2>{lesson.title}</h2>
        <p className="lesson-summary">{lesson.summary}</p>
        <MarkdownLite source={lesson.content} />
      </article>
      <div className="lesson-actions">
        {lesson.completed ? (
          <span className="pill-ok"><CheckCircle size={13} /> Lesson completed</span>
        ) : (
          <button className="btn-primary-action" onClick={complete} disabled={!lesson.unlocked}>
            <CheckCircle size={15} /> Mark lesson complete (+{lesson.xp_reward} XP)
          </button>
        )}
        {lesson.task && (
          <button className="btn-secondary-action" onClick={() => onNavigate({ view: "task", taskId: lesson.task!.id })}>
            Practice: {lesson.task.title} <ChevronRight size={15} />
          </button>
        )}
        {notice && <span className="notice-text">{notice}</span>}
      </div>
    </div>
  );
};

/* -------------------------------------------------------------- task view */
const TaskView: React.FC<{
  taskId: string;
  onNavigate: (t: AcademyTarget) => void;
  onOpenAuth: () => void;
  onOpenChallenge: (id: string) => void;
}> = ({ taskId, onNavigate, onOpenAuth, onOpenChallenge }) => {
  const { isAuthenticated, refreshProfile } = useAuth();
  const { theme } = useTheme();
  const [task, setTask] = useState<CourseTaskDetail | null>(null);
  const [code, setCode] = useState("");
  const [stdin, setStdin] = useState("");
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [runResult, setRunResult] = useState<SqlRunResult | CodeRunTaskResult | null>(null);
  const [submitResult, setSubmitResult] = useState<CourseSubmitResult | null>(null);
  const [busy, setBusy] = useState<"run" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replayId, setReplayId] = useState<string | null>(null);

  const load = async () => {
    try {
      const t = await api.getCourseTask(taskId);
      setTask(t);
      return t;
    } catch (e: any) {
      setError(e.message);
      return null;
    }
  };

  useEffect(() => {
    setTask(null); setRunResult(null); setSubmitResult(null); setAnswers({}); setError(null);
    load().then((t) => {
      if (!t) return;
      setCode(t.starter_code || "");
      setStdin(t.visible_tests[0]?.stdin || "");
    });
  }, [taskId]);

  const run = async () => {
    if (!task) return;
    try {
      setBusy("run"); setError(null);
      setRunResult(await api.runCourseTask(task.id, code, stdin));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const submit = async () => {
    if (!task) return;
    if (!isAuthenticated) return onOpenAuth();
    try {
      setBusy("submit"); setError(null);
      const payload = task.task_type === "quiz"
        ? { answers: task.questions.map((q) => (answers[q.index] ?? -1)) }
        : { code };
      const r = await api.submitCourseTask(task.id, payload);
      setSubmitResult(r);
      if (r.passed) {
        if (r.xp_earned > 0 || r.badge_awarded) confetti({ particleCount: r.badge_awarded ? 160 : 70, spread: 70, origin: { y: 0.6 } });
        await refreshProfile();
      }
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const navigateTarget = (type: string, id: string) => {
    if (type === "course_task") onNavigate({ view: "task", taskId: id });
    else if (type === "course_lesson") onNavigate({ view: "lesson", lessonId: id });
    else if (type === "challenge") onOpenChallenge(id);
  };

  if (error && !task) return <div className="page-shell"><div className="inline-error">{error}</div></div>;
  if (!task) return <div className="page-loading"><div className="spinner"></div><p>Loading task…</p></div>;

  const isQuiz = task.task_type === "quiz";
  const quizFeedback: QuizFeedback[] = isQuiz && submitResult?.details?.questions ? submitResult.details.questions : [];

  return (
    <div className="page-shell wide">
      <button className="back-link" onClick={() => onNavigate({ view: "course", slug: task.course_slug })}>
        <ArrowLeft size={15} /> {task.course_title} · Level {task.level_number}: {task.level_title}
      </button>

      <div className={`task-layout ${isQuiz ? "quiz" : ""}`}>
        <section className="task-brief">
          <div className="task-brief-head">
            <span className="eyebrow">
              {task.kind === "practice" ? "Practice task" : task.kind === "final" ? "Final assessment" : "Level assessment"} · {task.concept}
            </span>
            <h2>{task.title}</h2>
            <div className="task-tags">
              <span className={`diff-badge diff-${task.difficulty.toLowerCase()}`}>{task.difficulty}</span>
              <span className="tag"><Clock size={12} /> {task.estimated_minutes} min</span>
              <span className="tag"><Zap size={12} /> +{task.xp_reward} XP</span>
              {task.completed && <span className="pill-ok"><CheckCircle size={12} /> Completed</span>}
              {task.attempts > 0 && <span className="tag">{task.attempts} attempt{task.attempts > 1 ? "s" : ""}</span>}
            </div>
          </div>
          {!task.unlocked && <div className="inline-warn"><Lock size={14} /> {task.lock_reason}</div>}
          <MarkdownLite source={task.prompt} />
          {task.lesson_id && (
            <button className="btn-ghost-sm" onClick={() => onNavigate({ view: "lesson", lessonId: task.lesson_id! })}>
              <BookOpen size={14} /> Re-read lesson: {task.lesson_title}
            </button>
          )}
          {task.task_type === "code" && task.visible_tests.length > 0 && (
            <div className="example-tests">
              <span className="dejavu-label">Examples ({task.hidden_test_count} hidden test{task.hidden_test_count === 1 ? "" : "s"} too)</span>
              {task.visible_tests.map((t, i) => (
                <div key={i} className="example-test">
                  <div><span>Input</span><pre className="md-code small"><code>{t.stdin || "(none)"}</code></pre></div>
                  <div><span>Expected output</span><pre className="md-code small"><code>{t.expected_output}</code></pre></div>
                </div>
              ))}
            </div>
          )}
          {task.task_type === "sql" && (
            <p className="assist-note">
              {task.is_modification_task
                ? "This task changes data. It is checked by inspecting the table afterwards. Every run uses a fresh copy of the dataset."
                : task.order_matters ? "Row order matters for this task." : "Row order does not matter; column names/aliases are not checked."}
            </p>
          )}
        </section>

        <section className="task-work">
          {isQuiz ? (
            <div className="quiz-form">
              {task.questions.map((q) => {
                const fb = quizFeedback.find((f) => f.index === q.index);
                return (
                  <fieldset key={q.index} className={`quiz-q ${fb ? (fb.correct ? "right" : "wrong") : ""}`}>
                    <legend>{q.index + 1}. {q.question}</legend>
                    {q.options.map((opt, oi) => (
                      <label key={oi} className={`quiz-opt ${fb?.correct_option === oi ? "answer" : ""}`}>
                        <input type="radio" name={`q${q.index}`} checked={answers[q.index] === oi}
                               onChange={() => setAnswers((a) => ({ ...a, [q.index]: oi }))} disabled={!task.unlocked} />
                        <span>{opt}</span>
                      </label>
                    ))}
                    {fb && <p className="quiz-explain">{fb.correct ? "Correct. " : "Incorrect. "}{fb.explanation}</p>}
                  </fieldset>
                );
              })}
              <div className="task-actions">
                <button className="btn-primary-action" onClick={submit} disabled={busy !== null || !task.unlocked}>
                  <Send size={15} /> {busy === "submit" ? "Checking…" : "Submit answers"}
                </button>
                <span className="assist-note">Pass mark: {task.pass_mark}%</span>
              </div>
            </div>
          ) : (
            <>
              <div className="task-editor">
                <Editor
                  height="100%"
                  language={task.task_type === "sql" ? "sql" : "c"}
                  theme={theme === "light" ? "vs" : "vs-dark"}
                  value={code}
                  onChange={(v) => setCode(v || "")}
                  options={{ fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false, automaticLayout: true, tabSize: 4, padding: { top: 10, bottom: 10 } }}
                />
              </div>
              {task.task_type === "code" && (
                <label className="stdin-inline">
                  <span>stdin for Run</span>
                  <textarea rows={2} value={stdin} onChange={(e) => setStdin(e.target.value)} />
                </label>
              )}
              <div className="task-actions">
                <button className="btn-secondary-action" onClick={run} disabled={busy !== null}>
                  <Play size={15} /> {busy === "run" ? "Running…" : task.task_type === "sql" ? "Run query" : "Run"}
                </button>
                <button className="btn-primary-action" onClick={submit} disabled={busy !== null || !task.unlocked}>
                  <Send size={15} /> {busy === "submit" ? "Verifying…" : "Submit"}
                </button>
              </div>
            </>
          )}

          {error && <div className="inline-error">{error}</div>}

          {runResult && !submitResult && <RunOutput result={runResult} />}

          {submitResult && (
            <div className={`submit-result ${submitResult.passed ? "pass" : "fail"}`}>
              <div className="submit-head">
                {submitResult.passed ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                <strong>
                  {submitResult.passed ? "Verified: passed" : submitResult.status}
                  {submitResult.score != null && ` · ${submitResult.score}%`}
                  {!isQuiz && submitResult.total_count > 0 && task.task_type === "code" && ` · ${submitResult.passed_count}/${submitResult.total_count} tests`}
                </strong>
                {submitResult.xp_earned > 0 && <span className="xp-tag big">+{submitResult.xp_earned} XP</span>}
                {submitResult.already_completed && <span className="tag">Already completed: no additional XP</span>}
              </div>

              {submitResult.badge_awarded && (
                <div className="badge-awarded">
                  <GraduationCap size={22} className="text-amber-400" />
                  <div>
                    <strong>{submitResult.badge_awarded.title}</strong>
                    <p>{submitResult.badge_awarded.description}. It now appears in Achievements.</p>
                  </div>
                </div>
              )}
              {submitResult.level_completed && !submitResult.course_completed && (
                <p className="notice-text">Level {task.level_number} complete. The next level is unlocked.</p>
              )}
              {submitResult.roadmap_days_completed && submitResult.roadmap_days_completed.length > 0 && (
                <p className="notice-text">
                  Roadmap: {submitResult.roadmap_days_completed.map((d) => `Day ${d.day_number} complete (+${d.xp_earned} XP)`).join(", ")}
                </p>
              )}

              {submitResult.error && <pre className="md-code small error"><code>{submitResult.error}</code></pre>}

              {task.task_type === "code" && submitResult.test_results.length > 0 && (
                <div className="test-cases-table">
                  {submitResult.test_results.map((tc) => (
                    <div key={tc.case_index} className={`test-row ${tc.passed ? "passed" : "failed"}`}>
                      <div className="tc-col case-num">
                        {tc.passed ? <CheckCircle size={14} className="text-emerald-400" /> : <AlertCircle size={14} className="text-rose-400" />}
                        <span>Test #{tc.case_index}</span>
                      </div>
                      <div className="tc-col"><span className="col-label">Input:</span><code>{tc.input || "(none)"}</code></div>
                      <div className="tc-col"><span className="col-label">Expected:</span><code>{tc.expected_output}</code></div>
                      <div className="tc-col"><span className="col-label">Actual:</span><code>{tc.actual_output}</code></div>
                    </div>
                  ))}
                </div>
              )}

              {task.task_type === "sql" && submitResult.details?.comparison && (
                <p className="assist-note">{submitResult.details.comparison.detail}</p>
              )}
              {task.task_type === "sql" && submitResult.details?.student?.ok && (
                <RunOutput result={{ kind: "sql", ...submitResult.details.student }} label="Your result" />
              )}

              {!submitResult.passed && submitResult.deja_vu && (
                <DejaVuPanel dejaVu={submitResult.deja_vu} onReplay={setReplayId} />
              )}
              {!submitResult.passed && submitResult.assistance && (
                <AssistancePanel
                  contextType="course_task"
                  contextId={task.id}
                  code={code}
                  initial={submitResult.assistance}
                  hintsAllowed={task.hints_available}
                  onNavigate={navigateTarget}
                />
              )}
            </div>
          )}
        </section>
      </div>

      {replayId && <MemoryReplayView occurrenceId={replayId} onClose={() => setReplayId(null)} />}
    </div>
  );
};

const RunOutput: React.FC<{ result: SqlRunResult | CodeRunTaskResult; label?: string }> = ({ result, label }) => {
  if (result.kind === "sql") {
    if (!result.ok) return <pre className="md-code small error"><code>{result.error}</code></pre>;
    return (
      <div className="sql-result">
        <span className="dejavu-label">{label || "Query result"} · {result.rows?.length ?? 0} row(s){result.truncated ? " (truncated)" : ""}</span>
        <div className="md-table-wrap">
          <table className="md-table">
            <thead><tr>{result.columns?.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
            <tbody>
              {result.rows?.map((r, i) => (
                <tr key={i}>{r.map((v, j) => <td key={j}>{v === null ? <em className="null-val">NULL</em> : String(v)}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  return (
    <div className="run-output">
      <span className="dejavu-label">{result.status} · {result.execution_time}s</span>
      {result.compile_output && <pre className="md-code small error"><code>{result.compile_output}</code></pre>}
      {result.stdout && <pre className="md-code small"><code>{result.stdout}</code></pre>}
      {result.stderr && <pre className="md-code small error"><code>{result.stderr}</code></pre>}
      {!result.stdout && !result.stderr && !result.compile_output && <p className="assist-note">No output.</p>}
    </div>
  );
};
