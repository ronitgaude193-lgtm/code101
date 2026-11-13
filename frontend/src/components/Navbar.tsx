import React, { useEffect, useRef, useState } from "react";
import confetti from "canvas-confetti";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { Award, BarChart2, Flame, User, LogOut, Code, Compass, GraduationCap, Map, Brain, Sun, Moon, Zap } from "lucide-react";
import { Mascot } from "./Mascot";

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onOpenAuth: () => void;
}

// guarded tabs need an account; guests get the sign-in modal instead
const TABS = [
  { id: "playground", label: "Playground", icon: Code, guarded: false },
  { id: "challenges", label: "Challenges", icon: Compass, guarded: false },
  { id: "academy", label: "Academy", icon: GraduationCap, guarded: false },
  { id: "roadmap", label: "Roadmap", icon: Map, guarded: true },
  { id: "memory", label: "Memory", icon: Brain, guarded: true },
  { id: "dashboard", label: "Dashboard", icon: BarChart2, guarded: true },
  { id: "achievements", label: "Achievements", icon: Award, guarded: true },
];

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, onOpenAuth }) => {
  const { profile, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  // Celebrate XP the moment the profile reports it, wherever it was earned.
  const [pop, setPop] = useState<string | null>(null);
  const prev = useRef<{ xp: number; level: number } | null>(null);
  useEffect(() => {
    if (!profile) { prev.current = null; return; }
    const before = prev.current;
    prev.current = { xp: profile.total_xp, level: profile.current_level };
    if (!before || profile.total_xp <= before.xp) return;
    const levelUp = profile.current_level > before.level;
    setPop(levelUp ? `Level ${profile.current_level}!` : `+${profile.total_xp - before.xp} XP`);
    if (levelUp) confetti({ particleCount: 140, spread: 80, origin: { y: 0.3 } });
    const t = setTimeout(() => setPop(null), 2600);
    return () => clearTimeout(t);
  }, [profile]);

  return (
    <>
      <aside className="side-nav">
        <button className="brand" onClick={() => setCurrentTab(isAuthenticated ? "playground" : "landing")} aria-label="AI Coding Mentor home">
          <Mascot size={38} />
          <span className="brand-title">Coding Mentor</span>
        </button>
        <nav className="nav-links" aria-label="Main">
          {TABS.map(({ id, label, icon: Icon, guarded }) => (
            <button
              key={id}
              className={`nav-item ${currentTab === id ? "active" : ""}`}
              aria-current={currentTab === id ? "page" : undefined}
              aria-label={label}
              title={label}
              onClick={() => (guarded && !isAuthenticated ? onOpenAuth() : setCurrentTab(id))}
            >
              <Icon size={24} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <header className="hud">
        {isAuthenticated && profile ? (
          <div className="user-stats">
            <div className="stat-pill streak" title="Daily coding streak" aria-label={`${profile.streak_days} day streak`}>
              <Flame size={22} />
              <span>{profile.streak_days}</span>
            </div>

            <div className="stat-pill xp" title={`${100 - (profile.total_xp % 100)} XP to level ${profile.current_level + 1}`}>
              <span className="lv-badge" aria-label={`Level ${profile.current_level}`}>{profile.current_level}</span>
              {/* 100 XP per level, same rule as the backend */}
              <span className="xp-bar" aria-label={`${profile.total_xp % 100} of 100 XP to next level`}>
                <span style={{ width: `${profile.total_xp % 100}%` }} />
              </span>
              <span className="xp-num">{profile.total_xp} XP</span>
            </div>

            <div className="user-dropdown">
              <div className="user-info">
                <User size={18} />
                <span className="user-name">{profile.full_name}</span>
              </div>
              <button className="logout-btn" onClick={() => { logout(); setCurrentTab("landing"); }} title="Sign out" aria-label="Sign out">
                <LogOut size={18} />
              </button>
            </div>
          </div>
        ) : (
          <button className="btn-primary-auth" onClick={onOpenAuth}>Sign in</button>
        )}
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div aria-live="polite">{pop && <div className="xp-pop"><Zap size={18} /> {pop}</div>}</div>
      </header>
    </>
  );
};
