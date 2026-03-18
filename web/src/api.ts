import type { RunSummary, RunDetail } from "./types";

const BASE = import.meta.env.DEV ? "http://localhost:8080" : "";

export async function fetchRuns(): Promise<RunSummary[]> {
  const res = await fetch(`${BASE}/api/runs`);
  return res.json();
}

export async function fetchRun(dirName: string): Promise<RunDetail> {
  const res = await fetch(`${BASE}/api/runs/${dirName}`);
  return res.json();
}
