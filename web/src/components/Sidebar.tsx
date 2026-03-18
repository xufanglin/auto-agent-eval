import type { RunSummary } from "../types";
import { formatTimestamp } from "../utils";

interface Props {
  runs: RunSummary[];
  selectedDir: string | null;
  onSelect: (dirName: string) => void;
  loading: boolean;
}

export function Sidebar({ runs, selectedDir, onSelect, loading }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">🧪 Agent Eval</div>
      <div className="sidebar-list">
        {loading && <div className="sidebar-empty">Loading...</div>}
        {!loading && runs.length === 0 && <div className="sidebar-empty">No results yet</div>}
        {runs.map((run) => {
          const pct = Math.round(run.overall.score * 100);
          const active = selectedDir === run.dir_name;
          return (
            <div
              key={run.dir_name}
              className={`sidebar-item ${active ? "active" : ""}`}
              onClick={() => onSelect(run.dir_name)}
            >
              <div className="sidebar-item-top">
                <span className="sidebar-suite">{run.suite}</span>
                <span className={`sidebar-score ${pct >= 80 ? "good" : pct >= 50 ? "mid" : "bad"}`}>
                  {pct}%
                </span>
              </div>
              <div className="sidebar-item-bottom">
                <span className="sidebar-agents">{run.agents.join(", ")}</span>
                <span className="sidebar-time">{formatTimestamp(run.timestamp)}</span>
              </div>
              <div className="sidebar-item-bar">
                <div
                  className="sidebar-item-bar-fill"
                  style={{
                    width: `${pct}%`,
                    background: pct >= 80 ? "var(--green)" : pct >= 50 ? "var(--yellow)" : "var(--red)",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
