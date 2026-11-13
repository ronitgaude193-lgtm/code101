import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import { Play, Send, RotateCcw, Terminal, AlertCircle, CheckCircle, Clock, ChevronDown, ChevronUp } from "lucide-react";
import { CodeRunResult, CodeSubmitResult } from "../types";
import { useTheme } from "../context/ThemeContext";

interface MonacoPlaygroundProps {
  code: string;
  onChange: (value: string) => void;
  onRun: () => void;
  onSubmit: () => void;
  onReset: () => void;
  isRunning: boolean;
  isSubmitting: boolean;
  runResult: CodeRunResult | null;
  submitResult: CodeSubmitResult | null;
  hasChallenge: boolean;
  activeBottomTab: "terminal" | "debugger" | "autopsy";
  setActiveBottomTab: (tab: "terminal" | "debugger" | "autopsy") => void;
  bottomPanelContent?: React.ReactNode;
  /** Optional Déjà Vu / learning-strain panel shown above failed test results */
  learningInsights?: React.ReactNode;
}

export const MonacoPlayground: React.FC<MonacoPlaygroundProps> = ({
  code,
  onChange,
  onRun,
  onSubmit,
  onReset,
  isRunning,
  isSubmitting,
  runResult,
  submitResult,
  hasChallenge,
  activeBottomTab,
  setActiveBottomTab,
  bottomPanelContent,
  learningInsights,
}) => {
  const { theme } = useTheme();
  const [stdin, setStdin] = useState<string>("");
  const [showStdin, setShowStdin] = useState<boolean>(false);
  const [language, setLanguage] = useState<string>("python");

  return (
    <div className="playground-center">
      {/* Editor Header Bar */}
      <div className="editor-toolbar">
        <div className="toolbar-left">
          <select
            className="lang-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="python">Python 3 (Active)</option>
            <option value="javascript" disabled>JavaScript (Planned)</option>
            <option value="cpp" disabled>C++ (Planned)</option>
            <option value="java" disabled>Java (Planned)</option>
          </select>
          <span className="editor-status-tag">Monaco IDE v0.52</span>
        </div>

        <div className="toolbar-actions">
          <button
            className="btn-stdin"
            onClick={() => setShowStdin(!showStdin)}
            title="Provide standard input (stdin)"
          >
            {showStdin ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            <span>Stdin</span>
          </button>

          <button className="btn-tool" onClick={onReset} title="Reset code to initial template">
            <RotateCcw size={14} />
            <span>Reset</span>
          </button>

          <button
            className="btn-run"
            onClick={onRun}
            disabled={isRunning || isSubmitting}
            title="Execute code (Ctrl+Enter)"
          >
            <Play size={15} />
            <span>{isRunning ? "Running..." : "Run Code"}</span>
          </button>

          {hasChallenge && (
            <button
              className="btn-submit"
              onClick={onSubmit}
              disabled={isRunning || isSubmitting}
              title="Submit solution to challenge test cases"
            >
              <Send size={15} />
              <span>{isSubmitting ? "Testing..." : "Submit Solution"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Stdin Drawer */}
      {showStdin && (
        <div className="stdin-container">
          <div className="stdin-header">Standard Input (stdin):</div>
          <textarea
            className="stdin-input"
            rows={2}
            placeholder="Type input passed to input() calls here..."
            value={stdin}
            onChange={(e) => setStdin(e.target.value)}
          />
        </div>
      )}

      {/* Monaco Editor Container */}
      <div className="editor-container">
        <Editor
          height="100%"
          defaultLanguage="python"
          language={language}
          theme={theme === "light" ? "vs" : "vs-dark"}
          value={code}
          onChange={(val) => onChange(val || "")}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            lineNumbers: "on",
            bracketPairColorization: { enabled: true },
            suggestOnTriggerCharacters: true,
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>

      {/* Bottom Panel Navigation */}
      <div className="bottom-panel-wrapper">
        <div className="bottom-tabs-header">
          <div className="tabs-left">
            <button
              className={`tab-btn ${activeBottomTab === "terminal" ? "active" : ""}`}
              onClick={() => setActiveBottomTab("terminal")}
            >
              <Terminal size={15} />
              <span>Output Console</span>
            </button>

            <button
              className={`tab-btn ${activeBottomTab === "debugger" ? "active" : ""}`}
              onClick={() => setActiveBottomTab("debugger")}
            >
              <RotateCcw size={15} />
              <span>Visual Execution Tracer</span>
            </button>

            <button
              className={`tab-btn ${activeBottomTab === "autopsy" ? "active" : ""}`}
              onClick={() => setActiveBottomTab("autopsy")}
            >
              <AlertCircle size={15} />
              <span>AI Code Autopsy</span>
            </button>
          </div>

          {/* Quick status pill */}
          <div className="tabs-right">
            {runResult && (
              <div className={`status-badge ${runResult.exit_code === 0 ? "success" : "error"}`}>
                {runResult.exit_code === 0 ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
                <span>{runResult.status}</span>
                <span className="duration">
                  <Clock size={11} /> {runResult.execution_time}s
                </span>
              </div>
            )}
            {submitResult && (
              <div className={`status-badge ${submitResult.all_passed ? "success" : "error"}`}>
                {submitResult.all_passed ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
                <span>
                  {submitResult.all_passed
                    ? "Accepted (All Passed)"
                    : `${submitResult.passed_count}/${submitResult.total_count} Passed`}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Content Area */}
        <div className="bottom-content-area">
          {activeBottomTab === "terminal" && (
            <div className="terminal-console">
              {submitResult ? (
                <div className="submission-eval-view">
                  <div className="eval-summary">
                    <span className="eval-status-title">
                      {submitResult.all_passed ? "🎉 Challenge Completed Successfully!" : "⚠️ Test Cases Failed"}
                    </span>
                    <span className="eval-counts">
                      Score: {submitResult.passed_count} of {submitResult.total_count} tests passed
                    </span>
                    {submitResult.xp_earned > 0 && (
                      <span className="eval-xp">+{submitResult.xp_earned} XP Awarded</span>
                    )}
                  </div>

                  {learningInsights}

                  <div className="test-cases-table">
                    {submitResult.test_results.map((tc, idx) => (
                      <div key={idx} className={`test-row ${tc.passed ? "passed" : "failed"}`}>
                        <div className="tc-col case-num">
                          {tc.passed ? <CheckCircle size={14} className="tc-icon text-emerald-400" /> : <AlertCircle size={14} className="tc-icon text-rose-400" />}
                          <span>Test Case #{tc.case_index}</span>
                        </div>
                        <div className="tc-col">
                          <span className="col-label">Input:</span>
                          <code>{tc.input}</code>
                        </div>
                        <div className="tc-col">
                          <span className="col-label">Expected:</span>
                          <code>{tc.expected_output}</code>
                        </div>
                        <div className="tc-col">
                          <span className="col-label">Actual:</span>
                          <code>{tc.actual_output}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : runResult ? (
                <div className="terminal-output">
                  {runResult.stdout && <pre className="stdout-text">{runResult.stdout}</pre>}
                  {runResult.stderr && <pre className="stderr-text">{runResult.stderr}</pre>}
                  {!runResult.stdout && !runResult.stderr && (
                    <div className="text-muted">Program finished with exit code {runResult.exit_code} (No output produced).</div>
                  )}
                </div>
              ) : (
                <div className="terminal-placeholder">
                  Click <strong>Run Code</strong> or press <code>Ctrl+Enter</code> to execute Python. Output will appear here.
                </div>
              )}
            </div>
          )}

          {activeBottomTab !== "terminal" && bottomPanelContent}
        </div>
      </div>
    </div>
  );
};
