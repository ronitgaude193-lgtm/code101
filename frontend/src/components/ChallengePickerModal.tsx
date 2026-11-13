import React, { useEffect, useMemo, useRef, useState } from "react";
import { Search, X, CheckCircle, Award, Lock, Users, User } from "lucide-react";
import { ChallengeSummary } from "../types";

interface ChallengePickerModalProps {
  challenges: ChallengeSummary[];
  currentId?: string;
  onSelect: (id: string) => void;
  onClose: () => void;
}

const LEVELS = ["All", "Beginner", "Intermediate", "Advanced"];

/** Searchable pop-up replacing the challenge <select>, so it scales to many challenges. */
export const ChallengePickerModal: React.FC<ChallengePickerModalProps> = ({ challenges, currentId, onSelect, onClose }) => {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("All");
  const [mineOnly, setMineOnly] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    searchRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return challenges.filter((c) =>
      (level === "All" || c.difficulty === level) &&
      (!mineOnly || c.is_mine) &&
      (!q || c.title.toLowerCase().includes(q) || c.topic.toLowerCase().includes(q))
    );
  }, [challenges, query, level, mineOnly]);

  const solved = challenges.filter((c) => c.solved).length;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="picker-modal" role="dialog" aria-modal="true" aria-label="Choose a challenge" onClick={(e) => e.stopPropagation()}>
        <div className="picker-head">
          <div>
            <h3>Choose a challenge</h3>
            <p>{solved}/{challenges.length} solved</p>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="picker-progress" aria-hidden="true">
          <div style={{ width: `${challenges.length ? (100 * solved) / challenges.length : 0}%` }} />
        </div>

        <div className="picker-filters">
          <label className="picker-search">
            <Search size={15} />
            <input ref={searchRef} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by name or topic…" aria-label="Search challenges" />
          </label>
          <div className="difficulty-pills">
            {LEVELS.map((l) => (
              <button key={l} className={`filter-pill ${level === l ? "active" : ""}`} onClick={() => setLevel(l)}>{l}</button>
            ))}
            <button className={`filter-pill ${mineOnly ? "active" : ""}`} onClick={() => setMineOnly((m) => !m)}>
              <User size={12} /> Mine
            </button>
          </div>
        </div>

        <div className="picker-grid">
          {shown.map((c) => (
            <button
              key={c.id}
              className={`picker-card diff-edge-${c.difficulty.toLowerCase()} ${c.id === currentId ? "current" : ""} ${c.solved ? "solved" : ""}`}
              onClick={() => { onSelect(c.id); onClose(); }}
            >
              <div className="picker-card-top">
                <span className={`diff-badge diff-${c.difficulty.toLowerCase()}`}>{c.difficulty}</span>
                {c.is_mine && (c.visibility === "private"
                  ? <span className="vis-tag private"><Lock size={11} /> Only you</span>
                  : <span className="vis-tag shared"><Users size={11} /> Shared by you</span>)}
                {c.solved && <CheckCircle size={15} className="text-emerald-400 picker-check" aria-label="Solved" />}
              </div>
              <span className="picker-title">{c.title}</span>
              <span className="picker-meta">{c.topic} · <Award size={11} /> +{c.xp_reward} XP</span>
            </button>
          ))}
          {shown.length === 0 && <p className="assist-note">No challenges match these filters.</p>}
        </div>
      </div>
    </div>
  );
};
