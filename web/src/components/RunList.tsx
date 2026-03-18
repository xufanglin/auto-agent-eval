import type { RunSummary } from "../types";
import { ScoreBar } from "./ScoreBar";
import { formatTimestamp } from "../utils";

interface Props {
  runs: RunSummary[];
  onSelect: (dirName: string) => void;
}

export function RunList({ runs, onSelect }: Props) {
  if (runs.length === 0) {
    return <div className="empty">No evaluation results yet.</div>;
  }

  return (
    <div className="run-list">
      {runs.map((run) => (
        <div key={run.dir_name} className="run-card" onClick={() => onSelect(run.dir_name)}>
          <div className="run-card-header">
            <span className="run-suite">{run.suite}</span>
            <span className="run-time">{formatTimestamp(run.timestamp)}</span>
          </div>
          <div className="run-card-score">
            <ScoreBar score={run.overall.score} />
            <span className="run-pass-count">
              {run.overall.passed}/{run.overall.total} passed
            </span>
          </div>
          <div className="run-card-meta">
            <span className="tag agent-tag">{run.agents.join(", ")}</span>
            {Object.keys(run.by_category).map((cat) => (
              <span key={cat} className="tag cat-tag">{cat}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
