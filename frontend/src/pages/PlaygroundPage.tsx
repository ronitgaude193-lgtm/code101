import React, { useState, useEffect } from "react";
import confetti from "canvas-confetti";
import { api } from "../api/client";
import { ChallengeDetail, ChallengeSummary, CodeRunResult, CodeSubmitResult, VisualTraceResult, AIMentorResult, AutopsyResult } from "../types";
import { ChallengeSidebar } from "../components/ChallengeSidebar";
import { MonacoPlayground } from "../components/MonacoPlayground";
import { AICodingMentor } from "../components/AICodingMentor";
import { VisualDebugger } from "../components/VisualDebugger";
import { AICodeAutopsy } from "../components/AICodeAutopsy";
import { useAuth } from "../context/AuthContext";
import { DejaVuPanel } from "../components/DejaVuPanel";
import { AssistancePanel } from "../components/AssistancePanel";
import { MemoryReplayView } from "../components/MemoryReplayView";

interface PlaygroundPageProps {
  initialChallengeId?: string | null;
  onOpenGenerator: () => void;
  onOpenAuth: () => void;
  onNavigate?: (targetType: string, targetId: string) => void;
}

export const PlaygroundPage: React.FC<PlaygroundPageProps> = ({
  initialChallengeId,
  onOpenGenerator,
  onOpenAuth,
  onNavigate,
}) => {
  const { isAuthenticated, refreshProfile } = useAuth();

  // State
  const [allChallenges, setAllChallenges] = useState<ChallengeSummary[]>([]);
  const [currentChallenge, setCurrentChallenge] = useState<ChallengeDetail | null>(null);
  const [code, setCode] = useState<string>("# Write your Python code here\nprint('Hello, AI Coding Mentor!')\n");

  // Bottom Tabs
  const [activeBottomTab, setActiveBottomTab] = useState<"terminal" | "debugger" | "autopsy">("terminal");

  // Execution States
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<CodeRunResult | null>(null);
  const [submitResult, setSubmitResult] = useState<CodeSubmitResult | null>(null);

  // Visual Tracing States
  const [traceResult, setTraceResult] = useState<VisualTraceResult | null>(null);
  const [isTracing, setIsTracing] = useState<boolean>(false);

  // AI Mentor States
  const [mentorResult, setMentorResult] = useState<AIMentorResult | null>(null);
  const [isMentoring, setIsMentoring] = useState<boolean>(false);

  // Autopsy States
  const [autopsyResult, setAutopsyResult] = useState<AutopsyResult | null>(null);
  const [isAutopsying, setIsAutopsying] = useState<boolean>(false);

  // Mistake Memory replay
  const [replayId, setReplayId] = useState<string | null>(null);

  // Load all challenges on mount
  useEffect(() => {
    loadChallenges();
  }, []);

  // When initialChallengeId changes or loads
  useEffect(() => {
    if (initialChallengeId) {
      loadSpecificChallenge(initialChallengeId);
    }
  }, [initialChallengeId]);

  const loadChallenges = async () => {
    try {
      const data = await api.getChallenges();
      setAllChallenges(data);
      if (!initialChallengeId && data.length > 0 && !currentChallenge) {
        loadSpecificChallenge(data[0].id);
      }
    } catch {
      //
    }
  };

  const loadSpecificChallenge = async (id: string) => {
    try {
      const ch = await api.getChallenge(id);
      setCurrentChallenge(ch);
      setCode(ch.initial_code || "# Write your solution here\n");
      setSubmitResult(null);
      setRunResult(null);
      setTraceResult(null);
      setAutopsyResult(null);
      setMentorResult(null);
    } catch {
      //
    }
  };

  // Run Code
  const handleRunCode = async () => {
    try {
      setIsRunning(true);
      setActiveBottomTab("terminal");
      const res = await api.runCode(code, "python");
      setRunResult(res);
      setSubmitResult(null);
    } catch (err: any) {
      setRunResult({
        stdout: "",
        stderr: err.message,
        exit_code: 1,
        execution_time: 0.0,
        status: "Execution Error",
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Submit Challenge
  const handleSubmitCode = async () => {
    if (!currentChallenge) return;
    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }

    try {
      setIsSubmitting(true);
      setActiveBottomTab("terminal");
      const res = await api.submitCode(currentChallenge.id, code, "python");
      setSubmitResult(res);

      if (res.all_passed) {
        // Trigger celebratory confetti
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.6 },
        });
        await refreshProfile();
      } else {
        // Automatically suggest running autopsy
      }
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reset Code
  const handleResetCode = () => {
    if (currentChallenge) {
      setCode(currentChallenge.initial_code);
    } else {
      setCode("# Write your Python code here\nprint('Hello, AI Coding Mentor!')\n");
    }
    setRunResult(null);
    setSubmitResult(null);
  };

  // Visual Trace
  const handleRunTrace = async () => {
    try {
      setIsTracing(true);
      setActiveBottomTab("debugger");
      const res = await api.traceCode(code);
      setTraceResult(res);
    } catch (err: any) {
      setTraceResult({
        success: false,
        steps: [],
        total_steps: 0,
        error: err.message,
        output: "",
      });
    } finally {
      setIsTracing(false);
    }
  };

  // AI Mentor
  const handleAskMentor = async (mode: "learning" | "debugging" | "hint", prompt?: string) => {
    try {
      setIsMentoring(true);
      const res = await api.askMentor({
        code,
        language: "python",
        mode,
        prompt,
        challenge_id: currentChallenge?.id,
        execution_output: runResult?.stdout || submitResult?.status,
        error_message: runResult?.stderr,
      });
      setMentorResult(res);
    } catch (err: any) {
      alert(`AI Mentor communication error: ${err.message}`);
    } finally {
      setIsMentoring(false);
    }
  };

  // AI Code Autopsy
  const handleRunAutopsy = async () => {
    try {
      setIsAutopsying(true);
      setActiveBottomTab("autopsy");
      const res = await api.runAutopsy({
        code,
        language: "python",
        challenge_id: currentChallenge?.id,
        expected_behavior: currentChallenge?.test_cases[0]?.expected_output,
        actual_output: runResult?.stdout || submitResult?.test_results[0]?.actual_output,
        error_message: runResult?.stderr,
      });
      setAutopsyResult(res);
    } catch (err: any) {
      alert(`Autopsy analysis error: ${err.message}`);
    } finally {
      setIsAutopsying(false);
    }
  };

  return (
    <div className="playground-layout">
      {/* LEFT: Challenge & Specs */}
      <ChallengeSidebar
        challenge={currentChallenge}
        allChallenges={allChallenges}
        onSelectChallenge={loadSpecificChallenge}
        onOpenGenerator={onOpenGenerator}
      />

      {/* CENTER: Monaco Editor & Output/Tracer/Autopsy Console */}
      <MonacoPlayground
        code={code}
        onChange={setCode}
        onRun={handleRunCode}
        onSubmit={handleSubmitCode}
        onReset={handleResetCode}
        isRunning={isRunning}
        isSubmitting={isSubmitting}
        runResult={runResult}
        submitResult={submitResult}
        hasChallenge={!!currentChallenge}
        activeBottomTab={activeBottomTab}
        setActiveBottomTab={setActiveBottomTab}
        learningInsights={
          submitResult && !submitResult.all_passed && currentChallenge ? (
            <div className="insights-stack">
              {submitResult.deja_vu && <DejaVuPanel dejaVu={submitResult.deja_vu} onReplay={setReplayId} />}
              {submitResult.assistance && (
                <AssistancePanel
                  contextType="challenge"
                  contextId={currentChallenge.id}
                  code={code}
                  initial={submitResult.assistance}
                  onNavigate={(type, id) => (type === "challenge" ? loadSpecificChallenge(id) : onNavigate?.(type, id))}
                />
              )}
            </div>
          ) : null
        }
        bottomPanelContent={
          activeBottomTab === "debugger" ? (
            <VisualDebugger
              traceResult={traceResult}
              isLoading={isTracing}
              onRefreshTrace={handleRunTrace}
            />
          ) : activeBottomTab === "autopsy" ? (
            <AICodeAutopsy
              autopsyResult={autopsyResult}
              isLoading={isAutopsying}
              onRunAutopsy={handleRunAutopsy}
            />
          ) : null
        }
      />

      {/* RIGHT: AI Coding Mentor */}
      <AICodingMentor
        mentorResult={mentorResult}
        isLoading={isMentoring}
        onAskMentor={handleAskMentor}
      />

      {replayId && <MemoryReplayView occurrenceId={replayId} onClose={() => setReplayId(null)} />}
    </div>
  );
};
