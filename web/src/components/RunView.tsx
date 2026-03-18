import { useState } from "react";
import type { RunDetail, TaskDetail } from "../types";
import { ScoreBar } from "./ScoreBar";
import { TaskView } from "./TaskView";
import { formatTimestamp } from "../utils";

interface Props {
  run: RunDetail;
  onBack: () => void;
}

export function RunView({ run, onBack }: Props) {
  const [expandedTask, setExpandedTask] = useState<string | null>(null);

  return (
    <div className="run-view">
      <button className="back-btn" onClick={onBack}>← Back</button>

      <div className="run-header">
        <h2>{run.suite}</h2>
        <span className="run-time">{formatTimestamp(run.timestamp)}</span>
      </div>

      <div className="run-overall">
        <div className="score-big">
          <span className="score-number">{Math.round(run.overall.score * 100)}%</span>
          <span className="score-label">
            {run.overall.passed}/{run.overall.total} passed
          </span>
        </div>
        <div className="breakdown">
          <div className="breakdown-section">
            <h4>By Agent</h4>
            {Object.entries(run.by_agent).map(([agent, score]) => (
              <div key={agent} className="breakdown-row">
                <span>{agent}</span>
                <ScoreBar score={score} />
              </div>
            ))}
          </div>
          <div className="breakdown-section">
            <h4>By Category</h4>
            {Object.entries(run.by_category).map(([cat, score]) => (
              <div key={cat} className="breakdown-row">
                <span>{cat}</span>
                <ScoreBar score={score} />
              </div>
            ))}
          </div>
        </div>
      </div>

      <h3>Tasks</h3>
      <div className="task-list">
        {run.runs.map((entry) => {
          const detail: TaskDetail | undefined = run.task_details[entry.task];
          const wsKey = `${entry.agent}/${entry.task}`;
          const files = run.workspaces?.[wsKey] || [];
          const log = run.logs?.[wsKey] || "";
          const isExpanded = expandedTask === `${entry.agent}-${entry.task}`;
          const expandKey = `${entry.agent}-${entry.task}`;
          return (
            <div key={expandKey} className="task-card">
              <div
                className="task-card-header"
                onClick={() => setExpandedTask(isExpanded ? null : expandKey)}
              >
                <span className={`status-icon ${entry.passed ? "pass" : "fail"}`}>
                  {entry.passed ? "✅" : "❌"}
                </span>
                <span className="task-name">{entry.task}</span>
                <span className="task-agent">{entry.agent}</span>
                <ScoreBar score={entry.score} />
                <span className="task-duration">{entry.duration.toFixed(1)}s</span>
                <span className="expand-icon">{isExpanded ? "▼" : "▶"}</span>
              </div>
              {isExpanded && detail && (
                <TaskView detail={detail} files={files} log={log} dirName={run.dir_name} agent={entry.agent} task={entry.task} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
