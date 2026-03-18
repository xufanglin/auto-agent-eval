import { useState } from "react";
import type { TaskDetail } from "../types";

interface Props {
  detail: TaskDetail;
}

export function TaskView({ detail }: Props) {
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);
  const { metrics } = detail.result;

  return (
    <div className="task-detail">
      {metrics.map((m) => {
        const isExpanded = expandedMetric === m.metric_id;
        return (
          <div key={m.metric_id} className={`metric ${m.passed ? "metric-pass" : "metric-fail"}`}>
            <div
              className="metric-header"
              onClick={() => setExpandedMetric(isExpanded ? null : m.metric_id)}
            >
              <span>{m.passed ? "✅" : "❌"}</span>
              <span className="metric-name">{m.metric_name}</span>
              <span className="metric-score">{Math.round(m.score * 100)}%</span>
              {m.reason && <span className="expand-icon">{isExpanded ? "▼" : "▶"}</span>}
            </div>
            {isExpanded && m.reason && (
              <pre className="metric-reason">{m.reason}</pre>
            )}
          </div>
        );
      })}
    </div>
  );
}
