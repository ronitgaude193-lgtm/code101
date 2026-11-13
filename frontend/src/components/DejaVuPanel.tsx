import React from "react";
import { History, Repeat, Sparkles, Lightbulb, PlayCircle } from "lucide-react";
import { DejaVu } from "../types";

interface DejaVuPanelProps {
  dejaVu: DejaVu;
  onReplay?: (occurrenceId: string) => void;
}

/** Déjà Vu: shows whether the current mistake repeats (or relates to) a stored one. */
export const DejaVuPanel: React.FC<DejaVuPanelProps> = ({ dejaVu, onReplay }) => {
  const { status, current, previous } = dejaVu;
  const title =
    status === "repeat"
      ? `Déjà Vu: you've made this mistake before (${dejaVu.occurrences}×)`
      : status === "related"
      ? `Related mistake: same concept (${dejaVu.related_concept})`
      : "New mistake recorded in your Mistake Memory";

  return (
    <div className={`dejavu-panel dejavu-${status}`} role="status">
      <div className="dejavu-head">
        {status === "repeat" ? <Repeat size={16} /> : status === "related" ? <History size={16} /> : <Sparkles size={16} />}
        <strong>{title}</strong>
      </div>

      <div className="dejavu-grid">
        <div className="dejavu-col">
          <span className="dejavu-label">Current mistake</span>
          <span className="dejavu-category">{current.category}</span>
          <span className="dejavu-concept">Concept: {current.concept}</span>
          <p className="dejavu-text">{current.explanation}</p>
        </div>

        {previous ? (
          <div className="dejavu-col">
            <span className="dejavu-label">
              Previous mistake · {previous.when}
              {previous.resolved && <span className="pill-ok">fixed</span>}
            </span>
            <span className="dejavu-category">{previous.category}</span>
            <span className="dejavu-concept">In: {previous.context_title}</span>
            {previous.suggested_correction && <p className="dejavu-text">Correction then: {previous.suggested_correction}</p>}
            {previous.fixed_code_snippet && (
              <details className="dejavu-fix">
                <summary>How you fixed it last time</summary>
                <pre className="md-code"><code>{previous.fixed_code_snippet}</code></pre>
              </details>
            )}
          </div>
        ) : (
          <div className="dejavu-col muted">
            <span className="dejavu-label">History</span>
            <p className="dejavu-text">No earlier mistake of this kind. If it happens again, Mistake Memory will connect the two.</p>
          </div>
        )}
      </div>

      <div className="dejavu-rec">
        <Lightbulb size={14} />
        <span>{dejaVu.recommendation}</span>
      </div>

      {onReplay && (
        <button className="btn-ghost-sm" onClick={() => onReplay(dejaVu.occurrence_id)}>
          <PlayCircle size={14} /> Memory Replay: generic vs personalised feedback
        </button>
      )}
    </div>
  );
};
