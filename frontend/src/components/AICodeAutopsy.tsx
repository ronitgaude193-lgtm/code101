import React from "react";
import { Search, AlertTriangle, ArrowRight, Lightbulb, Repeat, BookOpen } from "lucide-react";
import { AutopsyResult } from "../types";

interface AICodeAutopsyProps {
  autopsyResult: AutopsyResult | null;
  isLoading: boolean;
  onRunAutopsy: () => void;
}

export const AICodeAutopsy: React.FC<AICodeAutopsyProps> = ({
  autopsyResult,
  isLoading,
  onRunAutopsy,
}) => {
  if (isLoading) {
    return (
      <div className="autopsy-empty">
        <div className="spinner"></div>
        <p>Conducting AI Forensic Code Autopsy...</p>
      </div>
    );
  }

  if (!autopsyResult) {
    return (
      <div className="autopsy-empty">
        <Search size={28} className="text-cyan-400" />
        <h4>AI Code Autopsy</h4>
        <p>Uncover WHY your code produced an unexpected answer rather than simply copying a solution.</p>
        <button className="btn-primary-action" onClick={onRunAutopsy}>
          Dissect & Diagnose Code
        </button>
      </div>
    );
  }

  return (
    <div className="autopsy-container">
      {/* Autopsy Header diagnosis */}
      <div className="autopsy-header-card">
        <div className="diagnosis-top">
          <div className="badge-row">
            <span className="badge-pill type-pill">
              <AlertTriangle size={13} />
              {autopsyResult.syntax_vs_logic}
            </span>
            <span className="badge-pill misconception-pill">
              {autopsyResult.misconception_identified}
            </span>
            {autopsyResult.is_simulated && (
              <span className="badge-pill offline-pill" title="Running on local offline pedagogical engine">
                Offline Pedagogical Engine
              </span>
            )}
          </div>
          <h3 className="diagnosis-title">{autopsyResult.primary_failure_reason}</h3>
        </div>

        <p className="diagnosis-explanation">{autopsyResult.detailed_walkthrough}</p>
      </div>

      {/* Loop Timeline (if available) */}
      {autopsyResult.loop_timeline && autopsyResult.loop_timeline.length > 0 && (
        <div className="autopsy-section">
          <div className="section-title">
            <Repeat size={16} />
            <span>Loop Iteration Dissection</span>
          </div>

          <div className="iterations-timeline">
            {autopsyResult.loop_timeline.map((iter, idx) => (
              <div key={idx} className="iteration-card">
                <div className="iter-header">
                  <span className="iter-number">Iteration #{iter.iteration}</span>
                  <div className="iter-vars">
                    {Object.entries(iter.variable_states).map(([k, v]) => (
                      <span key={k} className="var-chip">
                        {k}: <code>{String(v)}</code>
                      </span>
                    ))}
                  </div>
                </div>

                <div className="iter-comparison">
                  <div className="what-happened">
                    <span className="sub-tag actual">Actual Machine State:</span>
                    <p>{iter.what_happened}</p>
                  </div>
                  {iter.expected_state && (
                    <div className="expected-happened">
                      <span className="sub-tag expected">Expected Conceptual State:</span>
                      <p>{iter.expected_state}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Guiding Hint & Practice Prompt */}
      <div className="autopsy-guidance-grid">
        <div className="guidance-box hint-box">
          <div className="box-title">
            <Lightbulb size={16} className="text-amber-400" />
            <span>Guiding Hint (Try it yourself)</span>
          </div>
          <p>{autopsyResult.guiding_hint}</p>
        </div>

        <div className="guidance-box practice-box">
          <div className="box-title">
            <BookOpen size={16} className="text-emerald-400" />
            <span>Targeted Follow-up Practice</span>
          </div>
          <p>{autopsyResult.practice_prompt}</p>
        </div>
      </div>
    </div>
  );
};
