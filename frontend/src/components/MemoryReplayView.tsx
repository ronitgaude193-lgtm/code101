import React, { useEffect, useState } from "react";
import { X, User, Users, Info } from "lucide-react";
import { api } from "../api/client";
import { MemoryReplayResult } from "../types";

interface MemoryReplayViewProps {
  occurrenceId: string;
  onClose: () => void;
}

/** Memory Replay: the same mistake explained generically vs with the student's own history. */
export const MemoryReplayView: React.FC<MemoryReplayViewProps> = ({ occurrenceId, onClose }) => {
  const [data, setData] = useState<MemoryReplayResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    api.memoryReplay(occurrenceId)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [occurrenceId]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="replay-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Memory Replay">
        <div className="replay-header">
          <div>
            <h3>Memory Replay</h3>
            <p>The same mistake, explained without and with your mistake history.</p>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        {error && <div className="inline-error">{error}</div>}
        {!data && !error && (
          <div className="page-loading compact"><div className="spinner"></div><p>Comparing feedback…</p></div>
        )}

        {data && (
          <>
            <div className="replay-current">
              <span className="dejavu-category">{data.current_mistake.category}</span>
              <span className="dejavu-concept">Concept: {data.current_mistake.concept} · {data.current_mistake.context_title}</span>
              {data.current_mistake.error_excerpt && <pre className="md-code small"><code>{data.current_mistake.error_excerpt}</code></pre>}
            </div>

            <div className="replay-compare">
              <div className="replay-col">
                <div className="replay-col-head"><Users size={15} /> Generic feedback <span className="src-tag">{data.generic.source === "llm" ? "Gemma" : "rules"}</span></div>
                <p className="replay-summary">{data.generic.summary}</p>
                <p className="replay-text">{data.generic.explanation}</p>
                {data.generic.hints && data.generic.hints.length > 0 && (
                  <ul className="md-list">{data.generic.hints.map((h, i) => <li key={i}>{h}</li>)}</ul>
                )}
              </div>

              <div className="replay-col personal">
                <div className="replay-col-head"><User size={15} /> Personalised feedback {data.personalized && <span className="src-tag">{data.personalized.source === "llm" ? "Gemma" : "rules"}</span>}</div>
                {data.first_time || !data.personalized ? (
                  <div className="first-time-state">
                    <Info size={16} />
                    <p>{data.first_time_message}</p>
                  </div>
                ) : (
                  <>
                    <p className="replay-summary">{data.personalized.summary}</p>
                    <p className="replay-text">{data.personalized.explanation}</p>
                    {data.personalized.what_to_do_differently && (
                      <p className="replay-action"><strong>This time:</strong> {data.personalized.what_to_do_differently}</p>
                    )}
                  </>
                )}
              </div>
            </div>

            {data.memory_used.length > 0 && (
              <div className="replay-memory">
                <span className="dejavu-label">Memory used ({data.memory_used.length} relevant item{data.memory_used.length > 1 ? "s" : ""}, not your whole history)</span>
                <ul>
                  {data.memory_used.map((m, i) => (
                    <li key={i}>
                      <span className={`relation-tag ${m.relation}`}>{m.relation}</span> {m.category} in <em>{m.context_title}</em> · {m.when}
                      {m.resolved && <span className="pill-ok">fixed</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
