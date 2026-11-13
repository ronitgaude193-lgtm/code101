import React, { useEffect, useState } from "react";
import { Brain, Repeat, CheckCircle, PlayCircle, Lightbulb, AlertCircle } from "lucide-react";
import { api } from "../api/client";
import { MemoryPatternsResult } from "../types";
import { MemoryReplayView } from "../components/MemoryReplayView";

export const MemoryPage: React.FC = () => {
  const [data, setData] = useState<MemoryPatternsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replayId, setReplayId] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api.getMistakePatterns().then((d) => {
      setData(d);
      if (d.patterns[0]) setOpen(d.patterns[0].pattern_id);
    }).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="page-shell"><div className="inline-error">{error}</div></div>;
  if (!data) return <div className="page-loading"><div className="spinner"></div><p>Loading Mistake Memory…</p></div>;

  return (
    <div className="page-shell wide">
      <div className="page-heading">
        <div>
          <h2><Brain size={22} className="text-purple-400" /> Intelligent Mistake Memory</h2>
          <p>Every failed attempt is classified and remembered, so repeated mistakes are recognised (Déjà Vu) and feedback can be personalised (Memory Replay).</p>
        </div>
        <div className="memory-stats">
          <div><span className="stat-val">{data.total_mistakes}</span><span className="stat-label">mistakes recorded</span></div>
          <div><span className="stat-val">{data.patterns.length}</span><span className="stat-label">distinct patterns</span></div>
          <div><span className="stat-val">{data.repeated_patterns}</span><span className="stat-label">repeated</span></div>
        </div>
      </div>

      {data.patterns.length === 0 ? (
        <div className="page-empty dash-card">
          <Lightbulb size={26} className="text-amber-400" />
          <h4>No mistakes recorded yet</h4>
          <p>When a submission fails, Mistake Memory records what went wrong. Repeat a mistake and it will be recognised here and in the editor.</p>
        </div>
      ) : (
        <div className="pattern-list">
          {data.patterns.map((p) => (
            <section key={p.pattern_id} className={`pattern-card ${p.is_repeated ? "repeated" : ""}`}>
              <button className="pattern-head" onClick={() => setOpen(open === p.pattern_id ? null : p.pattern_id)} aria-expanded={open === p.pattern_id}>
                {p.is_repeated ? <Repeat size={16} className="text-rose-400" /> : <AlertCircle size={16} className="text-amber-400" />}
                <div className="pattern-title">
                  <strong>{p.category}</strong>
                  <span>{p.concept} · {p.language.toUpperCase()}</span>
                </div>
                <span className={`count-pill ${p.is_repeated ? "hot" : ""}`}>{p.occurrences}×</span>
                {p.resolved_count > 0 && <span className="pill-ok"><CheckCircle size={12} /> fixed {p.resolved_count}×</span>}
              </button>

              {open === p.pattern_id && (
                <div className="pattern-body">
                  <p>{p.explanation}</p>
                  <p className="dejavu-rec"><Lightbulb size={14} /> <span>{p.suggested_correction}</span></p>
                  <div className="occurrence-list">
                    {p.recent_occurrences.map((o) => (
                      <div key={o.occurrence_id} className="occurrence">
                        <div className="occurrence-head">
                          <span>{o.context_title}</span>
                          <span className="tag">{o.when}</span>
                          {o.resolved && <span className="pill-ok">fixed</span>}
                          <button className="btn-ghost-sm" onClick={() => setReplayId(o.occurrence_id)}>
                            <PlayCircle size={14} /> Replay
                          </button>
                        </div>
                        {o.error_excerpt && <pre className="md-code small error"><code>{o.error_excerpt}</code></pre>}
                        <div className="occurrence-code">
                          {o.code_snippet && (
                            <details>
                              <summary>Code that failed</summary>
                              <pre className="md-code small"><code>{o.code_snippet}</code></pre>
                            </details>
                          )}
                          {o.fixed_code_snippet && (
                            <details>
                              <summary>Your fix</summary>
                              <pre className="md-code small"><code>{o.fixed_code_snippet}</code></pre>
                            </details>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          ))}
        </div>
      )}

      {replayId && <MemoryReplayView occurrenceId={replayId} onClose={() => setReplayId(null)} />}
    </div>
  );
};
