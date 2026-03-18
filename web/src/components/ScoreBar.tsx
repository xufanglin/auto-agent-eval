interface Props {
  score: number;
}

export function ScoreBar({ score }: Props) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "var(--green)" : pct >= 50 ? "var(--yellow)" : "var(--red)";
  return (
    <div className="score-bar">
      <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      <span className="score-bar-label">{pct}%</span>
    </div>
  );
}
