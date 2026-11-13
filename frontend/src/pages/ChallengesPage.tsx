import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import { ChallengeSummary } from "../types";
import { Compass, Sparkles, CheckCircle, Search, Award, ArrowRight, Lock, Users } from "lucide-react";

interface ChallengesPageProps {
  onSelectChallenge: (id: string) => void;
}

export const ChallengesPage: React.FC<ChallengesPageProps> = ({ onSelectChallenge }) => {
  const [challenges, setChallenges] = useState<ChallengeSummary[]>([]);
  const [filteredChallenges, setFilteredChallenges] = useState<ChallengeSummary[]>([]);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Generator Modal state
  const [showGenModal, setShowGenModal] = useState<boolean>(false);
  const [genTopic, setGenTopic] = useState<string>("Loops & Lists");
  const [genDifficulty, setGenDifficulty] = useState<string>("Beginner");
  const [genVisibility, setGenVisibility] = useState<"private" | "public">("private");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  useEffect(() => {
    loadChallenges();
  }, []);

  const loadChallenges = async () => {
    try {
      setIsLoading(true);
      const data = await api.getChallenges();
      setChallenges(data);
      setFilteredChallenges(data);
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let result = challenges;
    if (selectedDifficulty !== "All") {
      result = result.filter((c) => c.difficulty.toLowerCase() === selectedDifficulty.toLowerCase());
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) => c.title.toLowerCase().includes(q) || c.topic.toLowerCase().includes(q) || c.description.toLowerCase().includes(q)
      );
    }
    setFilteredChallenges(result);
  }, [selectedDifficulty, searchQuery, challenges]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsGenerating(true);
      const generated = await api.generateChallenge(genTopic, genDifficulty, genVisibility);
      setShowGenModal(false);
      await loadChallenges();
      onSelectChallenge(generated.id);
    } catch (err: any) {
      alert(`Challenge Generation Error: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="challenges-page-container">
      {/* Page Header */}
      <div className="challenges-page-header">
        <div>
          <h2>Coding Challenges Repository</h2>
          <p>Practice algorithmic reasoning, data structures, loops, and condition logic.</p>
        </div>

        <button className="btn-primary-action" onClick={() => setShowGenModal(true)}>
          <Sparkles size={16} />
          <span>AI Challenge Generator</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="filter-search-bar">
        <div className="search-wrap">
          <Search size={16} className="text-muted" />
          <input
            type="text"
            placeholder="Search by challenge name, topic, or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="difficulty-pills">
          {["All", "Beginner", "Intermediate", "Advanced"].map((diff) => (
            <button
              key={diff}
              className={`filter-pill ${selectedDifficulty === diff ? "active" : ""}`}
              onClick={() => setSelectedDifficulty(diff)}
            >
              {diff}
            </button>
          ))}
        </div>
      </div>

      {/* Challenges Grid */}
      {isLoading ? (
        <div className="page-loading">
          <div className="spinner"></div>
          <p>Loading coding challenges...</p>
        </div>
      ) : filteredChallenges.length === 0 ? (
        <div className="page-empty">
          <Compass size={32} className="text-muted" />
          <h4>No challenges found</h4>
          <p>Try clearing your search query or generate a new challenge tailored to this topic.</p>
        </div>
      ) : (
        <div className="challenges-grid">
          {filteredChallenges.map((ch) => (
            <div
              key={ch.id}
              className={`challenge-card diff-edge-${ch.difficulty.toLowerCase()} ${ch.solved ? "card-solved" : ""}`}
              onClick={() => onSelectChallenge(ch.id)}
            >
              <div className="card-top-row">
                <span className={`diff-badge diff-${ch.difficulty.toLowerCase()}`}>
                  {ch.difficulty}
                </span>
                <span className="ch-topic-tag">{ch.topic}</span>
                {ch.is_mine && (ch.visibility === "private"
                  ? <span className="vis-tag private"><Lock size={11} /> Only you</span>
                  : <span className="vis-tag shared"><Users size={11} /> Shared by you</span>)}
                {ch.solved && (
                  <span className="ch-solved-tag">
                    <CheckCircle size={14} /> Solved
                  </span>
                )}
              </div>

              <h4 className="ch-card-title">{ch.title}</h4>
              <p className="ch-card-desc">{ch.description}</p>

              <div className="ch-card-footer">
                <span className="ch-xp-reward">
                  <Award size={14} className="text-amber-400" /> +{ch.xp_reward} XP
                </span>
                <button className="btn-solve-now">
                  <span>Solve</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Generator Modal */}
      {showGenModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <div className="modal-icon">
                <Sparkles size={20} className="text-amber-300" />
              </div>
              <div>
                <h4>AI Challenge Generator</h4>
                <p>Create a verified programming problem customized to your current learning focus.</p>
              </div>
            </div>

            <form onSubmit={handleGenerate} className="modal-form">
              <div className="form-group">
                <label>Programming Topic:</label>
                <select value={genTopic} onChange={(e) => setGenTopic(e.target.value)}>
                  <option value="Loops & Lists">Loops & Iteration</option>
                  <option value="Strings">Strings & Character Analysis</option>
                  <option value="Conditions">Conditions & Boolean Logic</option>
                  <option value="Functions">Functions & Decomposition</option>
                  <option value="Recursion">Recursion & State Trees</option>
                  <option value="Data Structures">Data Structures & Dictionaries</option>
                </select>
              </div>

              <div className="form-group">
                <label>Difficulty Level:</label>
                <select value={genDifficulty} onChange={(e) => setGenDifficulty(e.target.value)}>
                  <option value="Beginner">Beginner (Foundations)</option>
                  <option value="Intermediate">Intermediate (Logic & Edge Cases)</option>
                  <option value="Advanced">Advanced (Efficiency & Algorithms)</option>
                </select>
              </div>

              <fieldset className="form-group visibility-choice">
                <legend>Who can see this challenge?</legend>
                <label className={`vis-option ${genVisibility === "private" ? "active" : ""}`}>
                  <input type="radio" name="visibility" checked={genVisibility === "private"} onChange={() => setGenVisibility("private")} />
                  <Lock size={16} />
                  <span><strong>Keep it to myself</strong><small>Only you can see and solve it.</small></span>
                </label>
                <label className={`vis-option ${genVisibility === "public" ? "active" : ""}`}>
                  <input type="radio" name="visibility" checked={genVisibility === "public"} onChange={() => setGenVisibility("public")} />
                  <Users size={16} />
                  <span><strong>Share with everyone</strong><small>Other learners will see it in their challenge list.</small></span>
                </label>
              </fieldset>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowGenModal(false)}
                  disabled={isGenerating}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary-action" disabled={isGenerating}>
                  {isGenerating ? "Synthesizing Problem..." : "Generate & Solve"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
