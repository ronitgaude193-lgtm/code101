import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { Achievement } from "../types";
import { Award, CheckCircle, Lock, Play, Search, Eye, Flame, Repeat, Zap, GraduationCap, Database } from "lucide-react";

export const AchievementsPage: React.FC = () => {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    loadAchievements();
  }, []);

  const loadAchievements = async () => {
    try {
      setIsLoading(true);
      const data = await api.getAchievements();
      setAchievements(data);
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  const getBadgeIcon = (iconName: string) => {
    switch (iconName.toLowerCase()) {
      case "play":
        return <Play size={22} className="text-emerald-400" />;
      case "award":
        return <Award size={22} className="text-amber-400" />;
      case "search":
        return <Search size={22} className="text-cyan-400" />;
      case "eye":
        return <Eye size={22} className="text-purple-400" />;
      case "flame":
        return <Flame size={22} className="text-rose-400" />;
      case "repeat":
        return <Repeat size={22} className="text-indigo-400" />;
      case "graduationcap":
        return <GraduationCap size={22} className="text-amber-400" />;
      case "database":
        return <Database size={22} className="text-cyan-400" />;
      default:
        return <Zap size={22} className="text-yellow-400" />;
    }
  };

  const unlockedCount = achievements.filter((a) => a.unlocked).length;

  return (
    <div className="achievements-page-container">
      {/* Header Banner */}
      <div className="achievements-banner">
        <div>
          <h2>Trophy shelf</h2>
          <p>Every badge here is earned by code you actually ran and passed.</p>
        </div>

        <div className="milestone-counter">
          <span className="unlocked-num">{unlockedCount}</span>
          <span className="total-num">/ {achievements.length} Unlocked</span>
        </div>
      </div>

      {isLoading ? (
        <div className="page-loading">
          <div className="spinner"></div>
          <p>Loading achievements...</p>
        </div>
      ) : (
        <>
        {achievements.some((a) => a.category === "course") && (
          <section className="course-badges">
            <h3 className="section-title"><GraduationCap size={18} className="text-amber-400" /> Course Completion Badges</h3>
            <div className="course-badge-grid">
              {achievements.filter((a) => a.category === "course").map((ach) => (
                <div key={ach.id} className={`course-badge-card ${ach.unlocked ? "unlocked" : "locked"}`}>
                  <div className="ach-icon-container lg">
                    {ach.unlocked ? getBadgeIcon(ach.badge_icon) : <Lock size={22} className="text-muted" />}
                  </div>
                  <div className="ach-details">
                    <span className="eyebrow">{ach.course_title}</span>
                    <h4 className="ach-title">{ach.title}</h4>
                    <p className="ach-desc">{ach.description}</p>
                    <div className="ach-status-row">
                      {ach.unlocked ? (
                        <span className="unlocked-tag">
                          <CheckCircle size={13} /> Completed {ach.unlocked_at ? new Date(ach.unlocked_at).toLocaleDateString() : ""}
                        </span>
                      ) : (
                        <span className="locked-tag">Course in progress</span>
                      )}
                      <span className="ach-xp-pill">+{ach.xp_reward} XP</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <h3 className="section-title">Milestones</h3>
          </section>
        )}
        <div className="achievements-grid">
          {achievements.filter((a) => a.category !== "course").map((ach) => (
            <div
              key={ach.id}
              className={`achievement-card ${ach.unlocked ? "unlocked" : "locked"}`}
            >
              <div className="ach-icon-container">
                {ach.unlocked ? (
                  getBadgeIcon(ach.badge_icon)
                ) : (
                  <Lock size={22} className="text-muted" />
                )}
              </div>

              <div className="ach-details">
                <div className="ach-title-row">
                  <h4 className="ach-title">{ach.title}</h4>
                  <span className="ach-xp-pill">+{ach.xp_reward} XP</span>
                </div>
                <p className="ach-desc">{ach.description}</p>

                <div className="ach-status-row">
                  {ach.unlocked ? (
                    <span className="unlocked-tag">
                      <CheckCircle size={13} /> Unlocked
                    </span>
                  ) : (
                    <span className="locked-tag">In Progress</span>
                  )}
                  {ach.unlocked && ach.unlocked_at && (
                    <span className="ach-date">{new Date(ach.unlocked_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        </>
      )}
    </div>
  );
};
