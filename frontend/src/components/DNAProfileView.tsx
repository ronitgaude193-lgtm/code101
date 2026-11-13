import React from "react";
import { Dna, ShieldCheck, TrendingUp, Compass, Award } from "lucide-react";
import { ProgrammingDNAResult } from "../types";

interface DNAProfileViewProps {
  dna: ProgrammingDNAResult;
}

export const DNAProfileView: React.FC<DNAProfileViewProps> = ({ dna }) => {
  const metrics = [
    { label: "Logical Thinking", score: dna.logical_thinking_score, color: "var(--accent-cyan)" },
    { label: "Debugging Skill", score: dna.debugging_skill_score, color: "var(--accent-purple)" },
    { label: "Code Correctness", score: dna.code_correctness_score, color: "var(--accent-emerald)" },
    { label: "Problem Solving Speed", score: dna.problem_solving_speed, color: "var(--accent-amber)" },
    { label: "Hint Independence", score: dna.hint_independence_score, color: "var(--accent-rose)" },
    { label: "Practice Consistency", score: dna.consistency_score, color: "var(--accent-indigo)" },
  ];

  return (
    <div className="dna-profile-card">
      <div className="dna-header">
        <div className="dna-title-row">
          <div className="dna-icon-wrap">
            <Dna size={22} className="text-cyan-400" />
          </div>
          <div>
            <h4 className="dna-title">Programming DNA Profile</h4>
            <span className="dna-sub">Derived from measurable code execution & submission history</span>
          </div>
        </div>

        <div className="archetype-badge">
          <Award size={15} className="text-amber-300" />
          <span>{dna.overall_dna_archetype}</span>
        </div>
      </div>

      {/* Metrics Bars */}
      <div className="dna-metrics-grid">
        {metrics.map((m, idx) => (
          <div key={idx} className="dna-metric-row">
            <div className="metric-header">
              <span className="metric-name">{m.label}</span>
              <span className="metric-val">{m.score}%</span>
            </div>
            <div className="metric-track">
              <div
                className="metric-fill"
                style={{ width: `${m.score}%`, backgroundColor: m.color }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {/* Strengths & Growth Areas */}
      <div className="dna-insights-grid">
        <div className="insight-column strengths">
          <div className="insight-header">
            <ShieldCheck size={15} className="text-emerald-400" />
            <span>Demonstrated Strengths</span>
          </div>
          <div className="tags-wrap">
            {dna.top_strengths.map((str, i) => (
              <span key={i} className="insight-tag strength-tag">{str}</span>
            ))}
          </div>
        </div>

        <div className="insight-column growth">
          <div className="insight-header">
            <TrendingUp size={15} className="text-cyan-400" />
            <span>Growth Focus Areas</span>
          </div>
          <div className="tags-wrap">
            {dna.key_growth_areas.map((area, i) => (
              <span key={i} className="insight-tag growth-tag">{area}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
