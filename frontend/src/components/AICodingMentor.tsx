import React, { useState } from "react";
import { Sparkles, HelpCircle, Bug, BookOpen, Send, Lightbulb, ChevronRight, Check } from "lucide-react";
import { AIMentorResult } from "../types";

interface AICodingMentorProps {
  mentorResult: AIMentorResult | null;
  isLoading: boolean;
  onAskMentor: (mode: "learning" | "debugging" | "hint", query?: string) => void;
}

export const AICodingMentor: React.FC<AICodingMentorProps> = ({
  mentorResult,
  isLoading,
  onAskMentor,
}) => {
  const [activeMode, setActiveMode] = useState<"learning" | "debugging" | "hint">("learning");
  const [customQuestion, setCustomQuestion] = useState<string>("");
  const [revealedHintIndex, setRevealedHintIndex] = useState<number>(0);

  const handleModeChange = (mode: "learning" | "debugging" | "hint") => {
    setActiveMode(mode);
    setRevealedHintIndex(0);
    onAskMentor(mode);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customQuestion.trim()) return;
    onAskMentor(activeMode, customQuestion);
    setCustomQuestion("");
  };

  return (
    <div className="mentor-sidebar">
      {/* Mentor Header */}
      <div className="mentor-header">
        <div className="mentor-title-row">
          <div className="mentor-avatar">
            <Sparkles size={18} className="text-amber-300" />
          </div>
          <div>
            <h4 className="mentor-name">AI Coding Mentor</h4>
            <span className="mentor-status">
              {mentorResult?.is_simulated ? "Pedagogical Rule Engine" : "LLM Active"}
            </span>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="mode-tabs">
          <button
            className={`mode-tab ${activeMode === "learning" ? "active" : ""}`}
            onClick={() => handleModeChange("learning")}
            title="Concepts & step-by-step logic"
          >
            <BookOpen size={13} />
            <span>Learning</span>
          </button>

          <button
            className={`mode-tab ${activeMode === "debugging" ? "active" : ""}`}
            onClick={() => handleModeChange("debugging")}
            title="Diagnose code errors and flaws"
          >
            <Bug size={13} />
            <span>Debugging</span>
          </button>

          <button
            className={`mode-tab ${activeMode === "hint" ? "active" : ""}`}
            onClick={() => handleModeChange("hint")}
            title="Progressive clues without giving away answer"
          >
            <Lightbulb size={13} />
            <span>Hints</span>
          </button>
        </div>
      </div>

      {/* Mentor Body / Feed */}
      <div className="mentor-feed">
        {isLoading ? (
          <div className="mentor-loading">
            <div className="pulse-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>Analyzing code structure and reasoning...</p>
          </div>
        ) : mentorResult ? (
          <div className="mentor-content">
            {/* Summary Banner */}
            <div className="mentor-summary-card">
              <h5>{mentorResult.summary}</h5>
              <p>{mentorResult.explanation}</p>
            </div>

            {/* Progressive Hints Section */}
            {mentorResult.hints && mentorResult.hints.length > 0 && (
              <div className="hints-container">
                <div className="hints-header">
                  <Lightbulb size={15} className="text-amber-400" />
                  <span>Progressive Hints</span>
                </div>

                <div className="hints-list">
                  {mentorResult.hints.map((hint, idx) => {
                    const isRevealed = idx <= revealedHintIndex;
                    return (
                      <div key={idx} className={`hint-card ${isRevealed ? "revealed" : "locked"}`}>
                        {isRevealed ? (
                          <div className="hint-revealed">
                            <span className="hint-num">Hint #{idx + 1}</span>
                            <p>{hint}</p>
                          </div>
                        ) : (
                          <button
                            className="btn-reveal-hint"
                            onClick={() => setRevealedHintIndex(idx)}
                          >
                            <span>Reveal Hint #{idx + 1}</span>
                            <ChevronRight size={14} />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Conceptual Takeaway */}
            <div className="takeaway-card">
              <span className="takeaway-label">Key Principle to Remember:</span>
              <p>{mentorResult.conceptual_takeaway}</p>
            </div>

            {/* Related Topics */}
            {mentorResult.related_topics && (
              <div className="related-topics">
                <span className="sub-title">Recommended Topics:</span>
                <div className="topic-tags">
                  {mentorResult.related_topics.map((t, i) => (
                    <span key={i} className="topic-tag">{t}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="mentor-intro">
            <HelpCircle size={28} className="text-muted" />
            <h5>Virtual Programming Classroom</h5>
            <p>
              Your AI Mentor guides you to think like a programmer rather than just copying answers.
            </p>
            <div className="intro-actions">
              <button className="btn-intro-action" onClick={() => onAskMentor("learning")}>
                Explain My Code
              </button>
              <button className="btn-intro-action" onClick={() => onAskMentor("debugging")}>
                Diagnose Mistakes
              </button>
              <button className="btn-intro-action" onClick={() => onAskMentor("hint")}>
                Get Progressive Hint
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Question Form */}
      <form className="mentor-input-form" onSubmit={handleCustomSubmit}>
        <input
          type="text"
          className="mentor-text-input"
          placeholder="Ask a question about your code..."
          value={customQuestion}
          onChange={(e) => setCustomQuestion(e.target.value)}
          disabled={isLoading}
        />
        <button type="submit" className="btn-send-question" disabled={isLoading || !customQuestion.trim()}>
          <Send size={15} />
        </button>
      </form>
    </div>
  );
};
