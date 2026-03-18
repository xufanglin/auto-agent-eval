import { useEffect, useState } from "react";
import { fetchRuns, fetchRun } from "./api";
import type { RunSummary, RunDetail } from "./types";
import { Sidebar } from "./components/Sidebar";
import { RunView } from "./components/RunView";

export default function App() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<RunDetail | null>(null);
  const [selectedDir, setSelectedDir] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuns().then((r) => { setRuns(r); setLoading(false); });
  }, []);

  const handleSelect = async (dirName: string) => {
    setSelectedDir(dirName);
    const detail = await fetchRun(dirName);
    setSelected(detail);
  };

  return (
    <div className="layout">
      <Sidebar runs={runs} selectedDir={selectedDir} onSelect={handleSelect} loading={loading} />
      <main className="content">
        {loading ? (
          <div className="empty">Loading...</div>
        ) : selected ? (
          <RunView run={selected} />
        ) : (
          <div className="empty">
            <div className="empty-icon">🧪</div>
            <div>Select an evaluation run from the sidebar</div>
          </div>
        )}
      </main>
    </div>
  );
}
