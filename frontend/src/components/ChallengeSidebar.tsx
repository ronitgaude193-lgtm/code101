import React, { useState } from "react";
import { BookOpen, CheckCircle, ChevronDown, Award, Compass, Sparkles, Lock } from "lucide-react";
import { ChallengeDetail, ChallengeSummary } from "../types";
import { ChallengePickerModal } from "./ChallengePickerModal";

interface ChallengeSidebarProps {
  challenge: ChallengeDetail | null;
  allChallenges: ChallengeSummary[];
  onSelectChallenge: (id: string) => void;
  onOpenGenerator: () => void;
}

export const ChallengeSidebar: React.FC<ChallengeSidebarProps> = ({
  challenge,
  allChallenges,
  onSelectChallenge,
  onOpenGenerator,
}) => {
  const [pickerOpen, setPickerOpen] = useState(false);

  if (!challenge) {
    return (
      <div className="challenge-sidebar empty">
        <Compass size={28} className="text-muted" />
        <h4>Select a Challenge</h4>
        <p>Pick a challenge to begin solving, or generate a tailored practice problem.</p>
        <button className="btn-primary-action" onClick={onOpenGenerator}>
          <Sparkles size={14} />
          <span>Generate Challenge</span>
        </button>
      </div>
    );
  }

  const difficultyClass =
    challenge.difficulty === "Beginner"
      ? "diff-beginner"
      : challenge.difficulty === "Intermediate"
      ? "diff-intermediate"
      : "diff-advanced";

  return (
    <div className="challenge-sidebar">
      {/* Switch Challenge Picker Header */}
      <div className="challenge-header-bar">
        <button className="challenge-selector picker-trigger" onClick={() => setPickerOpen(true)} aria-haspopup="dialog">
          {challenge.solved && <CheckCircle size={13} className="text-emerald-400" />}
          <span className="picker-trigger-label">{challenge.title}</span>
          <ChevronDown size={14} />
        </button>

        <button className="btn-gen-pill" onClick={onOpenGenerator} title="Create AI Challenge">
          <Sparkles size={13} />
          <span>New</span>
        </button>
      </div>

      {pickerOpen && (
        <ChallengePickerModal
          challenges={allChallenges}
          currentId={challenge.id}
          onSelect={onSelectChallenge}
          onClose={() => setPickerOpen(false)}
        />
      )}

      <div className="challenge-body">
        {/* Title & Metadata */}
        <div className="challenge-meta">
          <div className="badge-row">
            <span className={`diff-badge ${difficultyClass}`}>{challenge.difficulty}</span>
            <span className="topic-badge">{challenge.topic}</span>
            <span className="xp-badge">
              <Award size={13} /> +{challenge.xp_reward} XP
            </span>
            {challenge.solved && (
              <span className="solved-badge">
                <CheckCircle size={13} /> Solved
              </span>
            )}
            {challenge.is_mine && challenge.visibility === "private" && (
              <span className="vis-tag private"><Lock size={11} /> Only you</span>
            )}
          </div>
          <h3 className="challenge-title">{challenge.title}</h3>
        </div>

        {/* Description */}
        <div className="challenge-desc">
          <p>{challenge.description}</p>
        </div>

        {/* Constraints */}
        {challenge.constraints && (
          <div className="challenge-section constraints">
            <h5>Constraints:</h5>
            <p>{challenge.constraints}</p>
          </div>
        )}

        {/* Test Case Examples */}
        <div className="challenge-section test-cases-preview">
          <h5>Example Test Cases:</h5>
          <div className="test-examples-list">
            {challenge.test_cases
              .filter((tc) => !tc.hidden)
              .map((tc, idx) => (
                <div key={idx} className="example-box">
                  <div className="example-row">
                    <span className="ex-label">Input:</span>
                    <code>{tc.input}</code>
                  </div>
                  <div className="example-row">
                    <span className="ex-label">Output:</span>
                    <code>{tc.expected_output}</code>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Problem Solving Tips */}
        <div className="challenge-section solving-tips">
          <div className="tip-header">
            <BookOpen size={14} className="text-cyan-400" />
            <span>Problem-Solving Approach:</span>
          </div>
          <ul className="tips-list">
            <li>Read the input specifications and check edge cases first.</li>
            <li>Run code frequently using the <strong>Run Code</strong> button.</li>
            <li>Use the <strong>AI Mentor</strong> if stuck, or run the <strong>Visual Debugger</strong> to step through loops.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
