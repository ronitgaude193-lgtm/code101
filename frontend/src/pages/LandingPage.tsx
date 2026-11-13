import React, { useState } from "react";
import {
  Award, BarChart2, BookOpen, Brain, Check, CheckCircle, Code, Compass, Flame, GraduationCap, Lock, Map, Moon, Sun, XCircle,
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { Mascot } from "../components/Mascot";

interface LandingPageProps {
  /** Opens a tab; guarded tabs fall back to the sign-in modal for guests. */
  onOpenTab: (tab: string) => void;
  onOpenAuth: () => void;
}

// Level 1 of the real C course, shown as the path the Academy draws.
const DEMO_STEPS = [
  { kind: "lesson done", icon: Check, title: "Introduction to C & Program Structure", sub: "Lesson" },
  { kind: "task done", icon: Check, title: "Your first C program", sub: "Practice task" },
  { kind: "lesson current", icon: BookOpen, title: "Variables, Data Types & Input/Output", sub: "Lesson" },
  { kind: "task locked", icon: Lock, title: "Add two numbers", sub: "Practice task" },
  { kind: "assessment locked", icon: Lock, title: "Level 1 Assessment: Fundamentals", sub: "Pass it to unlock Level 2" },
];

const KIT = [
  { tab: "academy", icon: GraduationCap, name: "Academy", text: "Two courses, C Programming and DBMS & SQL, five levels each." },
  { tab: "playground", icon: Code, name: "Playground", text: "A real editor for Python with a step-by-step visual debugger." },
  { tab: "challenges", icon: Compass, name: "Challenges", text: "Practice problems by difficulty, or generate one on a topic you pick." },
  { tab: "roadmap", icon: Map, name: "Roadmap", text: "A 30-day plan that starts where you are and schedules reviews." },
  { tab: "memory", icon: Brain, name: "Mistake Memory", text: "Spots when you repeat an old mistake and shows how you fixed it last time." },
  { tab: "dashboard", icon: BarChart2, name: "Dashboard", text: "Skill mastery, weak spots and your Programming DNA profile." },
];

const PICKS = ["3.5", "3", "4"];
const ANSWER = "3";

export const LandingPage: React.FC<LandingPageProps> = ({ onOpenTab, onOpenAuth }) => {
  const { theme, toggleTheme } = useTheme();
  const [pick, setPick] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);
  const right = pick === ANSWER;

  return (
    <div className="landing">
      <div className="landing-inner">
        <header className="landing-bar">
          <div className="brand">
            <Mascot size={42} />
            <span className="brand-title">Coding Mentor</span>
          </div>
          <button className="theme-toggle" onClick={toggleTheme} aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button className="btn-secondary-action" onClick={onOpenAuth}>Sign in</button>
        </header>

        <section className="landing-hero">
          <div>
            <h1>Learn to code in small wins.</h1>
            <p>
              AI Coding Mentor teaches C, SQL and Python through short lessons, code that really runs,
              and a mentor that gives you hints instead of answers.
            </p>
            <div className="landing-cta">
              <button className="btn-primary-action lg" onClick={() => onOpenTab("academy")}>Get started</button>
              <button className="btn-secondary-action lg" onClick={onOpenAuth}>I already have an account</button>
            </div>
          </div>

          <div className="quiz-card">
            <Mascot size={72} bob />
            <h3>Try one. What does this print?</h3>
            <pre><code>{`int x = 7;\nprintf("%d", x / 2);`}</code></pre>
            <div className="quiz-picks" role="group" aria-label="Answers">
              {PICKS.map((p) => (
                <button key={p} className="quiz-pick" aria-pressed={pick === p} onClick={() => { setPick(p); setChecked(false); }}>
                  {p}
                </button>
              ))}
            </div>
            <div className="quiz-foot" aria-live="polite">
              {checked && (
                <span className={`quiz-verdict ${right ? "right" : "wrong"}`}>
                  {right ? <CheckCircle size={22} /> : <XCircle size={22} />}
                  {right ? "Correct. Two ints divide to an int." : "Not quite. Both are ints, so C drops the .5"}
                </span>
              )}
              {checked && right ? (
                <button className="btn-primary-action" onClick={() => onOpenTab("academy")}>Keep going</button>
              ) : (
                <button className="btn-primary-action" disabled={!pick} onClick={() => setChecked(true)}>Check</button>
              )}
            </div>
          </div>
        </section>
      </div>

      <div className="landing-band">
        <div className="landing-inner">
          <section className="landing-section">
            <div className="path" aria-label="Example: Level 1 of the C Programming course">
              <div className="unit">
                <div className="unit-banner">
                  <div>
                    <h3>Level 1 · Fundamentals</h3>
                    <p>C Programming</p>
                  </div>
                </div>
                <ol className="path-steps">
                  {DEMO_STEPS.map((s, i) => (
                    <li key={s.title} style={{ "--i": i } as React.CSSProperties}>
                      <div className={`step ${s.kind}`}>
                        {s.kind.includes("current") && <span className="node-bubble"><span>Start</span></span>}
                        <span className="node"><s.icon size={28} strokeWidth={3} /></span>
                        <span className="node-label">
                          <span className="lesson-title">{s.title}</span>
                          <span className="lesson-sub">{s.sub}</span>
                        </span>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
            <div>
              <h2>Every course is a path you can see.</h2>
              <p>
                Read a short lesson, then prove it with a practice task. C is compiled and tested with real input,
                SQL is checked against a reference query. Pass the level assessment and the next level opens.
              </p>
            </div>
          </section>
        </div>
      </div>

      <div className="landing-inner">
        <section className="landing-section">
          <div>
            <h2>Streaks, XP and levels keep score.</h2>
            <p>
              Lessons, tasks and challenges pay out XP, and every 100 XP is a new level. Come back daily to grow
              your streak, and collect a badge for each course you finish.
            </p>
          </div>
          <div className="hud-demo" aria-label="Example of the score bar">
            <span className="stat-pill streak"><Flame size={36} /> 5</span>
            <span className="stat-pill xp">
              <span className="lv-badge">3</span>
              <span className="xp-bar"><span style={{ width: "60%" }} /></span>
            </span>
            <span className="stat-pill" style={{ color: "var(--accent-amber)" }}><Award size={36} /> 4</span>
          </div>
        </section>
      </div>

      <div className="landing-band">
        <div className="landing-inner">
          <section className="kit">
            <h2>Six places to practise.</h2>
            <ul className="kit-list">
              {KIT.map((k) => (
                <li key={k.tab}>
                  <button className="kit-item" onClick={() => onOpenTab(k.tab)}>
                    <span className="node"><k.icon size={26} /></span>
                    <span>
                      <strong>{k.name}</strong>
                      <span>{k.text}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      <section className="landing-close">
        <Mascot size={84} bob />
        <h2>Pick a course and write your first program.</h2>
        <button className="btn-primary-action lg" onClick={() => onOpenTab("academy")}>Start learning</button>
      </section>

      <div className="landing-inner">
        <footer className="landing-foot">
          <span>AI Coding Mentor</span>
          <span>Try it without an account. Sign in to save XP and progress.</span>
        </footer>
      </div>
    </div>
  );
};
