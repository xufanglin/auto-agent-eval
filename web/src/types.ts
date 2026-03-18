export interface RunSummary {
  dir_name: string;
  suite: string;
  timestamp: string;
  agents: string[];
  tasks: string[];
  overall: { score: number; passed: number; total: number };
  by_agent: Record<string, number>;
  by_category: Record<string, number>;
  runs: RunEntry[];
}

export interface RunEntry {
  task: string;
  agent: string;
  score: number;
  passed: boolean;
  duration: number;
  status: string;
}

export interface MetricResult {
  metric_id: string;
  metric_name: string;
  score: number;
  passed: boolean;
  reason: string;
  raw_output: string;
}

export interface TaskDetail {
  id: string;
  task_id: string;
  agent_id: string;
  status: string;
  result: {
    score: number;
    passed: boolean;
    metrics: MetricResult[];
    duration_seconds: number;
    agent_output_length: number;
    timestamp: string;
  };
}

export interface RunDetail extends RunSummary {
  task_details: Record<string, TaskDetail>;
}
