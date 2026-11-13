import React, { useEffect, useState } from "react";
import { Activity, HelpCircle, Coffee, BookOpen, TrendingDown, ChevronRight } from "lucide-react";
import { api } from "../api/client";
import { ContextType, HintResult, RecoverySuggestion, StrainAssessment } from "../types";

interface AssistancePanelProps {
  contextType: ContextType;
  contextId: string;
  code: string;
  /** strain returned with the last submission (avoids an extra request) */
  initial?: StrainAssessment | null;
  hintsAllowed?: boolean;
  onNavigate?: (targetType: string, targetId: string) => void;
}

const HINT_LABELS = ["Conceptual", "Directional", "Guided"];

/** Learning-strain indicator, contextual hint offer, progressive hints and recovery suggestions. */
export const AssistancePanel: React.FC<AssistancePanelProps> = ({
  contextType, contextId, code, initial, hintsAllowed = true, onNavigate,
}) => {
  const [strain, setStrain] = useState<StrainAssessment | null>(initial || null);
  const [hints, setHints] = useState<HintResult[]>([]);
  const [recovery, setRecovery] = useState<RecoverySuggestion[]>(initial?.recovery || []);
  const [offerHandled, setOfferHandled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setStrain(initial || null);
    setRecovery(initial?.recovery || []);
    setOfferHandled(false);
  }, [initial]);

  useEffect(() => {
    setHints([]);
  }, [contextId]);

  if (!strain) return null;

  const requestHint = async () => {
    try {
      setBusy(true);
      setError(null);
      const h = await api.getNextHint(contextType, contextId, code);
      if (h.exhausted) setRecovery(h.recovery);
      else setHints((prev) => [...prev, h]);
      const s = await api.getStrain(contextType, contextId);
      setStrain(s);
      if (s.recovery.length) setRecovery(s.recovery);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const respond = async (accepted: boolean) => {
    setOfferHandled(true);
    try {
      await api.respondToHintOffer(contextType, contextId, accepted);
    } catch {
      // non-critical
    }
    if (accepted) await requestHint();
  };

  const nextLevel = strain.hints_used + hints.length + 1;
  const canAskMore = hintsAllowed && nextLevel <= 3 && !(hints.length && hints[hints.length - 1].hints_remaining === 0);

  return (
    <div className={`assist-panel strain-${strain.level}`}>
      <div className="assist-head">
        <Activity size={15} />
        <span className="assist-title">Learning strain</span>
        <div className="strain-meter" aria-label={`Learning strain ${strain.strain_score} of 100`}>
          <div className="strain-fill" style={{ width: `${strain.strain_score}%` }} />
        </div>
        <span className="strain-score">{strain.strain_score}/100 · {strain.level}</span>
      </div>

      {strain.signals.length > 0 && (
        <ul className="strain-signals">
          {strain.signals.map((s) => <li key={s.signal}>{s.detail} <span className="signal-pts">+{s.points}</span></li>)}
        </ul>
      )}

      {hintsAllowed && strain.offer_hint && !offerHandled && hints.length === 0 && (
        <div className="hint-offer">
          <HelpCircle size={16} />
          <span>{strain.message}</span>
          <div className="hint-offer-actions">
            <button className="btn-primary-sm" onClick={() => respond(true)} disabled={busy}>Yes, a small hint</button>
            <button className="btn-ghost-sm" onClick={() => respond(false)} disabled={busy}>No thanks</button>
          </div>
        </div>
      )}

      {hints.length > 0 && (
        <div className="hint-stack">
          {hints.map((h) => (
            <div key={h.level} className={`hint-card hint-l${h.level}`}>
              <span className="hint-level">Hint {h.level} · {h.level_name}</span>
              <p>{h.hint}</p>
            </div>
          ))}
        </div>
      )}

      {canAskMore && (offerHandled || hints.length > 0 || !strain.offer_hint) && (
        <button className="btn-ghost-sm" onClick={requestHint} disabled={busy}>
          <HelpCircle size={14} /> {busy ? "Thinking…" : `Get ${HINT_LABELS[nextLevel - 1].toLowerCase()} hint (${nextLevel}/3)`}
        </button>
      )}
      {!hintsAllowed && <p className="assist-note">Hints are not available during assessments.</p>}
      {error && <div className="inline-error">{error}</div>}

      {recovery.length > 0 && (
        <div className="recovery-list">
          <span className="dejavu-label">Suggestions</span>
          {recovery.map((r, i) => (
            <div key={i} className="recovery-item">
              {r.type === "break" ? <Coffee size={14} /> : r.type === "review" ? <BookOpen size={14} /> : <TrendingDown size={14} />}
              <div>
                <strong>{r.title}</strong>
                <p>{r.detail}</p>
              </div>
              {r.target_type && r.target_id && onNavigate && (
                <button className="icon-btn" onClick={() => onNavigate(r.target_type!, r.target_id!)} aria-label={`Open ${r.title}`}>
                  <ChevronRight size={16} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="assist-disclaimer">{strain.disclaimer}</p>
    </div>
  );
};
