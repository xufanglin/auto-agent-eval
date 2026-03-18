import { useState } from "react";
import type { TaskDetail, WorkspaceFile } from "../types";
import { fileUrl } from "../api";

interface Props {
  detail: TaskDetail;
  files: WorkspaceFile[];
  log: string;
  dirName: string;
  agent: string;
  task: string;
}

type Tab = "metrics" | "files" | "log";

export function TaskView({ detail, files, log, dirName, agent, task }: Props) {
  const [tab, setTab] = useState<Tab>("metrics");
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<{ path: string; content: string } | null>(null);

  const loadFile = async (path: string) => {
    if (fileContent?.path === path) { setFileContent(null); return; }
    const url = fileUrl(dirName, `${agent}/${task}/${path}`);
    const res = await fetch(url);
    const text = await res.text();
    setFileContent({ path, content: text });
  };

  const formatSize = (bytes: number) =>
    bytes < 1024 ? `${bytes}B` : `${(bytes / 1024).toFixed(1)}K`;

  return (
    <div className="task-detail">
      <div className="tab-bar">
        <button className={tab === "metrics" ? "active" : ""} onClick={() => setTab("metrics")}>
          Metrics ({detail.result.metrics.length})
        </button>
        {files.length > 0 && (
          <button className={tab === "files" ? "active" : ""} onClick={() => setTab("files")}>
            Files ({files.length})
          </button>
        )}
        {log && (
          <button className={tab === "log" ? "active" : ""} onClick={() => setTab("log")}>
            Agent Log
          </button>
        )}
      </div>

      {tab === "metrics" && detail.result.metrics.map((m) => {
        const isExpanded = expandedMetric === m.metric_id;
        return (
          <div key={m.metric_id} className={`metric ${m.passed ? "metric-pass" : "metric-fail"}`}>
            <div className="metric-header" onClick={() => setExpandedMetric(isExpanded ? null : m.metric_id)}>
              <span>{m.passed ? "✅" : "❌"}</span>
              <span className="metric-name">{m.metric_name}</span>
              <span className="metric-score">{Math.round(m.score * 100)}%</span>
              {m.reason && <span className="expand-icon">{isExpanded ? "▼" : "▶"}</span>}
            </div>
            {isExpanded && m.reason && <pre className="metric-reason">{m.reason}</pre>}
          </div>
        );
      })}

      {tab === "files" && (
        <div className="file-list">
          {files.filter(f => !f.path.startsWith(".originals/")).map((f) => (
            <div key={f.path} className="file-item">
              <div className="file-header" onClick={() => loadFile(f.path)}>
                <span className="file-icon">📄</span>
                <span className="file-path">{f.path}</span>
                <span className="file-size">{formatSize(f.size)}</span>
                <span className="expand-icon">{fileContent?.path === f.path ? "▼" : "▶"}</span>
              </div>
              {fileContent?.path === f.path && (
                <pre className="file-content">{fileContent.content}</pre>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === "log" && <pre className="agent-log">{log}</pre>}
    </div>
  );
}
