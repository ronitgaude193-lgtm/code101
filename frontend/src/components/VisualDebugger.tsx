import React, { useState, useEffect } from "react";
import { Play, Pause, SkipBack, SkipForward, RotateCcw, ListFilter, Layers, Eye } from "lucide-react";
import { VisualTraceResult, TraceStep } from "../types";

interface VisualDebuggerProps {
  traceResult: VisualTraceResult | null;
  isLoading: boolean;
  onRefreshTrace: () => void;
}

export const VisualDebugger: React.FC<VisualDebuggerProps> = ({
  traceResult,
  isLoading,
  onRefreshTrace,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(800);

  const steps: TraceStep[] = traceResult?.steps || [];
  const currentStep = steps[currentStepIndex] || null;

  // Auto-play interval
  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, playbackSpeed);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, steps.length, playbackSpeed]);

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  if (isLoading) {
    return (
      <div className="debugger-empty">
        <div className="spinner"></div>
        <p>Tracing execution inside isolated environment...</p>
      </div>
    );
  }

  if (!traceResult || steps.length === 0) {
    return (
      <div className="debugger-empty">
        <Eye size={28} className="text-muted" />
        <h4>Python Visual Execution Engine</h4>
        <p>Step through execution line by line, inspect variable state changes, and examine loop iterations.</p>
        <button className="btn-primary-action" onClick={onRefreshTrace}>
          Generate Execution Trace
        </button>
      </div>
    );
  }

  return (
    <div className="visual-debugger-container">
      {/* Playback Controls Bar */}
      <div className="debugger-controls-bar">
        <div className="step-counter">
          <span>Step</span>
          <strong>{currentStepIndex + 1}</strong>
          <span>of {steps.length}</span>
        </div>

        <div className="control-buttons">
          <button className="btn-dbg" onClick={handleReset} title="Reset to start">
            <RotateCcw size={14} />
          </button>
          <button className="btn-dbg" onClick={handlePrev} disabled={currentStepIndex === 0} title="Previous step">
            <SkipBack size={14} />
          </button>
          <button
            className="btn-dbg play-btn"
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? "Pause auto-playback" : "Play step-by-step"}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>
          <button className="btn-dbg" onClick={handleNext} disabled={currentStepIndex === steps.length - 1} title="Next step">
            <SkipForward size={14} />
          </button>
        </div>

        <div className="playback-speed-select">
          <label>Speed:</label>
          <select value={playbackSpeed} onChange={(e) => setPlaybackSpeed(Number(e.target.value))}>
            <option value={1200}>0.5x Slow</option>
            <option value={800}>1.0x Normal</option>
            <option value={400}>2.0x Fast</option>
          </select>
        </div>

        <div className="current-event-pill">
          <span className={`event-tag ${currentStep?.event || "line"}`}>
            {currentStep?.event.toUpperCase()} (Line {currentStep?.line})
          </span>
          <span className="func-tag">{currentStep?.func_name}()</span>
        </div>
      </div>

      {/* Main Inspection Grid: Left Variables, Right Call Stack & Output */}
      <div className="debugger-panels-grid">
        {/* Variables Table */}
        <div className="debugger-panel variables-panel">
          <div className="panel-title">
            <ListFilter size={15} />
            <span>Active Variables & State</span>
          </div>
          <div className="variables-table-wrapper">
            {currentStep && Object.keys(currentStep.variables).length > 0 ? (
              <table className="vars-table">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th>Type</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(currentStep.variables).map(([name, val], idx) => {
                    const valType = Array.isArray(val) ? "list" : typeof val;
                    return (
                      <tr key={idx} className="var-row">
                        <td className="var-name">
                          <code>{name}</code>
                        </td>
                        <td className="var-type">{valType}</td>
                        <td className="var-val">
                          <code>{JSON.stringify(val)}</code>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="panel-empty-text">No active local variables defined at this step.</div>
            )}
          </div>
        </div>

        {/* Stack and Stdout preview */}
        <div className="debugger-panel stack-panel">
          <div className="panel-title">
            <Layers size={15} />
            <span>Call Stack & Output So Far</span>
          </div>

          <div className="stack-content">
            <div className="stack-frames">
              <span className="sub-label">Call Stack:</span>
              <div className="frames-list">
                {currentStep?.stack && currentStep.stack.length > 0 ? (
                  currentStep.stack.map((frame, i) => (
                    <div key={i} className="frame-item">
                      <code>{frame}</code>
                    </div>
                  ))
                ) : (
                  <div className="frame-item">&lt;module&gt; (Top-level)</div>
                )}
              </div>
            </div>

            <div className="stdout-so-far">
              <span className="sub-label">Stdout So Far:</span>
              <pre className="stdout-preview">
                {currentStep?.stdout_so_far || "(no printed output yet)"}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
