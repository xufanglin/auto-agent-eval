import { useEffect, useState } from "react";
import { fetchRuns, fetchRun } from "./api";
import type { RunSummary, RunDetail } from "./types";
import { RunList } from "./components/RunList";
import { RunView } from "./components/RunView";

export default function App() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuns().then((r) => { setRuns(r); setLoading(false); });
  }, []);

  const handleSelect = async (dirName: string) => {
    setLoading(true);
    const detail = await fetchRun(dirName);
    setSelected(detail);
    setLoading(false);
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="app">
      <header>
        <h1 onClick={() => setSelected(null)} style={{ cursor: "pointer" }}>
          🧪 Agent Eval
        </h1>
      </header>
      <main>
        {selected ? (
          <RunView run={selected} onBack={() => setSelected(null)} />
        ) : (
          <RunList runs={runs} onSelect={handleSelect} />
        )}
      </main>
    </div>
  );
}
