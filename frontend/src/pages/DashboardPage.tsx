import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { DashboardData, Roadmap, CourseSummary } from "../types";
import { DNAProfileView } from "../components/DNAProfileView";
import { Award, CheckCircle, Flame, BarChart2, AlertCircle, ArrowRight, Zap, Target, History, Map, GraduationCap } from "lucide-react";

interface DashboardPageProps {
  onSelectChallenge: (id: string) => void;
  onOpenPlayground: () => void;
  onOpenRoadmap?: () => void;
  onOpenCourse?: (slug: string) => void;
  onNavigate?: (targetType: string, targetId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onSelectChallenge,
  onOpenPlayground,
  onOpenRoadmap,
  onOpenCourse,
  onNavigate,
}) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await api.getDashboard();
      setData(res);
      // Learning plan widgets are optional: the dashboard still loads if they fail.
      api.getRoadmap().then((r) => setRoadmap(r.roadmap)).catch(() => setRoadmap(null));
      api.getCourses().then(setCourses).catch(() => setCourses([]));
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page-loading">
        <div className="spinner"></div>
        <p>Loading your personalized learning dashboard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-error">
        <AlertCircle size={32} className="text-rose-400" />
        <h4>Dashboard Unavailable</h4>
        <p>{error || "Unable to retrieve student profile"}</p>
        <button className="btn-primary-action" onClick={loadDashboard}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Student Welcome Banner */}
      <div className="dashboard-banner">
        <div className="banner-text">
          <h2>Welcome back, {data.profile.full_name}!</h2>
          <p>
            You are currently on <strong>Level {data.profile.current_level}</strong> with{" "}
            <strong>{data.profile.total_xp} Total XP</strong>. Keep your daily momentum going!
          </p>
        </div>

        <div className="banner-quick-actions">
          <button className="btn-primary-action" onClick={onOpenPlayground}>
            Open Coding Playground <ArrowRight size={15} />
          </button>
        </div>
      </div>

      {/* Stats Summary Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrap bg-cyan">
            <Target size={20} className="text-cyan-400" />
          </div>
          <div className="stat-info">
            <span className="stat-val">{data.problems_attempted}</span>
            <span className="stat-label">Problems Attempted</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrap bg-emerald">
            <CheckCircle size={20} className="text-emerald-400" />
          </div>
          <div className="stat-info">
            <span className="stat-val">{data.problems_solved}</span>
            <span className="stat-label">Problems Solved</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrap bg-amber">
            <Flame size={20} className="text-amber-400" />
          </div>
          <div className="stat-info">
            <span className="stat-val">{data.profile.streak_days} Days</span>
            <span className="stat-label">Daily Streak</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrap bg-purple">
            <Zap size={20} className="text-purple-400" />
          </div>
          <div className="stat-info">
            <span className="stat-val">{data.solve_rate}%</span>
            <span className="stat-label">Solve Accuracy</span>
          </div>
        </div>
      </div>

      {/* Learning plan: today's roadmap task + course progress */}
      <div className="dashboard-columns-grid">
        <div className="dash-card">
          <div className="card-header">
            <Map size={18} className="text-cyan-400" />
            <h4>Today's Roadmap Task</h4>
          </div>
          {roadmap && roadmap.current_day ? (
            <div className="today-task">
              <span className="eyebrow">Day {roadmap.current_day.day_number} of {roadmap.total_days} · {roadmap.completed_days} completed</span>
              <h5>{roadmap.current_day.topic}</h5>
              <p>{roadmap.current_day.objective}</p>
              <div className="task-tags">
                <span className={`diff-badge diff-${roadmap.current_day.difficulty.toLowerCase()}`}>{roadmap.current_day.difficulty}</span>
                <span className="tag">{roadmap.current_day.estimated_minutes} min</span>
                <span className="tag">+{roadmap.current_day.xp_reward} XP</span>
              </div>
              <button className="btn-primary-action" onClick={() => onNavigate?.(roadmap.current_day!.linked_type, roadmap.current_day!.linked_id)}>
                Start today's task <ArrowRight size={15} />
              </button>
            </div>
          ) : (
            <div className="no-weakness-box">
              <Map size={22} className="text-cyan-400" />
              <p>{roadmap ? "Every day of your roadmap is complete. Generate a new one to keep going." : "You don't have a roadmap yet. Generate a 30-day plan personalised to your progress."}</p>
              <button className="btn-secondary-action" onClick={onOpenRoadmap}>Open Roadmap</button>
            </div>
          )}
        </div>

        <div className="dash-card">
          <div className="card-header">
            <GraduationCap size={18} className="text-amber-400" />
            <h4>Coding Academy Progress</h4>
          </div>
          <div className="skills-list">
            {courses.map((c) => (
              <button key={c.id} className="course-progress-row" onClick={() => onOpenCourse?.(c.slug)}>
                <div className="skill-meta">
                  <span className="skill-title">{c.title}</span>
                  <span className="stat-num">
                    {c.completed ? "Completed" : `${c.progress.levels_completed}/${c.progress.total_levels} levels · ${c.progress.percent}%`}
                  </span>
                </div>
                <div className="skill-bar-track">
                  <div className="skill-bar-fill" style={{ width: `${c.progress.percent}%` }}></div>
                </div>
              </button>
            ))}
            {courses.length === 0 && <p className="assist-note">Courses unavailable.</p>}
          </div>
        </div>
      </div>

      {/* Programming DNA Profile Card */}
      <DNAProfileView dna={data.programming_dna} />

      {/* Skills & Weaknesses Grid */}
      <div className="dashboard-columns-grid">
        {/* Left Column: Skill Mastery */}
        <div className="dash-card">
          <div className="card-header">
            <BarChart2 size={18} className="text-cyan-400" />
            <h4>Programming Skill Mastery</h4>
          </div>

          <div className="skills-list">
            {data.skills.map((skill, idx) => (
              <div key={idx} className="skill-row">
                <div className="skill-meta">
                  <span className="skill-title">{skill.skill_name}</span>
                  <div className="skill-stats-pill">
                    <span className="stat-num">{skill.problems_solved}/{skill.problems_attempted} Solved</span>
                    <span className={`status-badge ${skill.status.toLowerCase().replace(" ", "-")}`}>
                      {skill.status}
                    </span>
                  </div>
                </div>

                <div className="skill-bar-track">
                  <div
                    className="skill-bar-fill"
                    style={{ width: `${skill.mastery_level}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Weaknesses & Targeted Actions */}
        <div className="dash-card">
          <div className="card-header">
            <AlertCircle size={18} className="text-amber-400" />
            <h4>Identified Weaknesses & Next Steps</h4>
          </div>

          <div className="weakness-list">
            {data.weaknesses.length > 0 ? (
              data.weaknesses.map((w, idx) => (
                <div key={idx} className="weakness-card">
                  <div className="weakness-top">
                    <span className="weakness-topic">{w.topic}</span>
                    <span className="weakness-rate">Error Rate: {(w.error_rate * 100).toFixed(0)}%</span>
                  </div>
                  <p className="weakness-rec">{w.recommendation}</p>
                </div>
              ))
            ) : (
              <div className="no-weakness-box">
                <CheckCircle size={24} className="text-emerald-400" />
                <p>No critical conceptual weaknesses identified! Keep attempting new challenges to expand your skills.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommended Practice Challenges */}
      <div className="dash-card full-width">
        <div className="card-header">
          <Award size={18} className="text-amber-400" />
          <h4>Personalized Recommended Challenges</h4>
        </div>

        <div className="recommended-grid">
          {data.recommended_challenges.map((ch) => (
            <div key={ch.id} className="rec-challenge-card" onClick={() => onSelectChallenge(ch.id)}>
              <div className="rec-card-top">
                <span className="rec-topic">{ch.topic}</span>
                <span className={`diff-badge diff-${ch.difficulty.toLowerCase()}`}>
                  {ch.difficulty}
                </span>
              </div>
              <h5 className="rec-title">{ch.title}</h5>
              <p className="rec-desc">{ch.description}</p>
              <div className="rec-bottom">
                <span className="rec-xp">+{ch.xp_reward} XP</span>
                <button className="btn-solve-pill">Solve <ArrowRight size={13} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
