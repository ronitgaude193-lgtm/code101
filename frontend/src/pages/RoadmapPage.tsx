import React, { useEffect, useState } from "react";
import { Map, RefreshCw, CheckCircle, Circle, Clock, Zap, Target, BookOpen, Award, RotateCcw, Code, Sparkles, ChevronRight } from "lucide-react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Roadmap, RoadmapDay } from "../types";

interface RoadmapPageProps {
  onOpenCourseTask: (taskId: string) => void;
  onOpenLesson: (lessonId: string) => void;
  onOpenChallenge: (challengeId: string) => void;
}

const TRACKS: Array<{ id: "mixed" | "c" | "sql"; label: string; desc: string }> = [
  { id: "mixed", label: "C + DBMS & SQL", desc: "Alternate between programming and databases" },
  { id: "c", label: "C Programming", desc: "Focus on C fundamentals to structures" },
  { id: "sql", label: "DBMS & SQL", desc: "Focus on databases and SQL" },
];

const DayIcon: React.FC<{ type: RoadmapDay["day_type"] }> = ({ type }) =>
  type === "review" ? <RotateCcw size={14} /> : type === "assessment" ? <Award size={14} /> : type === "challenge" ? <Code size={14} /> : <BookOpen size={14} />;

export const RoadmapPage: React.FC<RoadmapPageProps> = ({ onOpenCourseTask, onOpenLesson, onOpenChallenge }) => {
  const { refreshProfile } = useAuth();
  const [roadmap, setRoadmap] = useState<Roadmap | null | undefined>(undefined);
  const [track, setTrack] = useState<"mixed" | "c" | "sql">("mixed");
  const [generating, setGenerating] = useState(false);
  const [selected, setSelected] = useState<RoadmapDay | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const r = await api.getRoadmap();
      setRoadmap(r.roadmap);
      if (r.roadmap) {
        setTrack(r.roadmap.track);
        setSelected((prev) => r.roadmap!.days.find((d) => d.id === prev?.id) || r.roadmap!.current_day || r.roadmap!.days[0] || null);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => { load(); }, []);

  const generate = async () => {
    if (roadmap && !window.confirm("Generate a new roadmap? Your current plan will be archived (XP you earned is kept).")) return;
    try {
      setGenerating(true);
      setError(null);
      const r = await api.generateRoadmap(track);
      setRoadmap(r.roadmap);
      setSelected(r.roadmap.current_day || r.roadmap.days[0] || null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const verify = async (day: RoadmapDay) => {
    try {
      const r = await api.completeRoadmapDay(day.id);
      setMessage(r.completed ? (r.xp_earned ? `${r.message} +${r.xp_earned} XP` : r.message) : r.message);
      if (r.completed) await refreshProfile();
      load();
    } catch (e: any) {
      setMessage(e.message);
    }
  };

  const openDay = (day: RoadmapDay) => {
    if (day.linked_type === "challenge") onOpenChallenge(day.linked_id);
    else onOpenCourseTask(day.linked_id);
  };

  if (roadmap === undefined && !error) {
    return <div className="page-loading"><div className="spinner"></div><p>Loading your roadmap…</p></div>;
  }

  return (
    <div className="page-shell wide">
      <div className="page-heading">
        <div>
          <h2><Map size={22} className="text-cyan-400" /> 30-Day Personalized Roadmap</h2>
          <p>A daily plan built from your progress, recorded mistakes and assessment results. It updates as you learn.</p>
        </div>
        {roadmap && (
          <button className="btn-secondary-action" onClick={generate} disabled={generating}>
            <RefreshCw size={15} /> {generating ? "Regenerating…" : "Regenerate"}
          </button>
        )}
      </div>

      {error && <div className="inline-error">{error}</div>}

      {!roadmap && (
        <div className="roadmap-empty dash-card">
          <Sparkles size={26} className="text-amber-400" />
          <h3>Create your roadmap</h3>
          <p>Choose a track. The plan starts where you are, schedules reviews for concepts you've struggled with, and links every day to a task that is verified when you complete it.</p>
          <div className="track-picker">
            {TRACKS.map((t) => (
              <button key={t.id} className={`track-option ${track === t.id ? "active" : ""}`} onClick={() => setTrack(t.id)}>
                <strong>{t.label}</strong>
                <span>{t.desc}</span>
              </button>
            ))}
          </div>
          <button className="btn-primary-action" onClick={generate} disabled={generating}>
            {generating ? "Building your plan…" : "Generate my 30-day roadmap"}
          </button>
        </div>
      )}

      {roadmap && (
        <>
          <div className="roadmap-summary dash-card">
            <div className="roadmap-progress">
              <div className="ring" style={{ ["--pct" as any]: `${roadmap.percent}` }}>
                <span>{roadmap.completed_days}/{roadmap.total_days}</span>
              </div>
              <div>
                <span className="eyebrow">{TRACKS.find((t) => t.id === roadmap.track)?.label} · started {roadmap.start_date}</span>
                <p className="roadmap-focus">{roadmap.focus_summary}</p>
                <div className="concept-chips">
                  {roadmap.priority_concepts.map((p) => (
                    <span key={p.concept} className="concept-chip" title={p.evidence}><Target size={12} /> {p.concept}</span>
                  ))}
                  <span className="tag"><Zap size={12} /> {roadmap.xp_earned} roadmap XP earned</span>
                  {roadmap.generated_with === "rules+llm" && <span className="tag">tips written by Gemma</span>}
                </div>
              </div>
            </div>
            {roadmap.total_days < 30 && (
              <p className="assist-note">Your remaining curriculum fits in {roadmap.total_days} days. Regenerate with another track for more.</p>
            )}
          </div>

          <div className="roadmap-layout">
            <ol className="roadmap-timeline">
              {roadmap.days.map((d) => (
                <li key={d.id}>
                  <button
                    className={`day-item ${d.completed ? "done" : ""} ${roadmap.current_day?.id === d.id ? "current" : ""} ${selected?.id === d.id ? "selected" : ""}`}
                    onClick={() => setSelected(d)}
                  >
                    <span className="day-num">{d.completed ? <CheckCircle size={15} /> : roadmap.current_day?.id === d.id ? <Circle size={15} className="text-cyan-400" /> : d.day_number}</span>
                    <span className="day-main">
                      <span className="day-topic">Day {d.day_number} · {d.topic}</span>
                      <span className="day-sub"><DayIcon type={d.day_type} /> {d.day_type} · {d.difficulty} · {d.estimated_minutes} min · +{d.xp_reward} XP</span>
                    </span>
                  </button>
                </li>
              ))}
            </ol>

            {selected && (
              <aside className="day-detail dash-card">
                <span className="eyebrow">Day {selected.day_number} · {selected.scheduled_date} · {selected.day_type}</span>
                <h3>{selected.topic}</h3>
                <div className="task-tags">
                  <span className={`diff-badge diff-${selected.difficulty.toLowerCase()}`}>{selected.difficulty}</span>
                  <span className="tag"><Clock size={12} /> {selected.estimated_minutes} min</span>
                  <span className="tag"><Zap size={12} /> +{selected.xp_reward} XP</span>
                  {selected.completed && <span className="pill-ok"><CheckCircle size={12} /> Completed</span>}
                </div>
                <h5>Objective</h5>
                <p>{selected.objective}</p>
                <h5>Explanation</h5>
                <p>{selected.explanation}</p>
                <h5>Practical task</h5>
                <p>{selected.task_description}</p>
                {selected.reason && <p className="day-reason"><Target size={13} /> {selected.reason}</p>}
                {selected.coach_tip && <p className="day-tip"><Sparkles size={13} /> {selected.coach_tip}</p>}
                <div className="task-actions">
                  {selected.lesson_id && (
                    <button className="btn-secondary-action" onClick={() => onOpenLesson(selected.lesson_id!)}>
                      <BookOpen size={15} /> Lesson
                    </button>
                  )}
                  <button className="btn-primary-action" onClick={() => openDay(selected)}>
                    {selected.linked_type === "challenge" ? "Open challenge" : "Open task"} <ChevronRight size={15} />
                  </button>
                  {!selected.completed && (
                    <button className="btn-ghost-sm" onClick={() => verify(selected)}>Verify completion</button>
                  )}
                </div>
                {message && <p className="notice-text">{message}</p>}
                <p className="assist-note">Days complete automatically once the linked task is verified. XP is awarded once per day.</p>
              </aside>
            )}
          </div>
        </>
      )}
    </div>
  );
};
