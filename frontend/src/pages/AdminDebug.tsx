import { useEffect, useState } from "react";
import { api, AdminMatchesResponse, PipelineMetricsResponse } from "../api/client";

export function AdminDebug() {
  const [matches, setMatches] = useState<AdminMatchesResponse | null>(null);
  const [metrics, setMetrics] = useState<PipelineMetricsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.getAdminMatches(), api.getPipelineMetrics()])
      .then(([matchData, metricData]) => {
        setMatches(matchData);
        setMetrics(metricData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load admin data"));
  }, []);

  return (
    <div className="page">
      <div className="hero compact">
        <span className="badge">Admin debug</span>
        <h1>Path A match quality</h1>
        <p className="hint">Review catalog matches and pipeline metrics (Phase 2).</p>
      </div>

      {error && <p className="error">{error}</p>}

      {metrics && (
        <div className="card">
          <h2>Pipeline metrics</h2>
          <h3>Path A (ingest)</h3>
          <ul className="metrics-list">
            <li>Runs: {metrics.path_a.runs}</li>
            <li>Avg shortlist: {metrics.path_a.avg_shortlist_size}</li>
            <li>Max LLM candidates: {metrics.path_a.max_llm_candidate_size}</li>
          </ul>
          <h3>Path B (checkout)</h3>
          <ul className="metrics-list">
            <li>Runs: {metrics.path_b.runs}</li>
            <li>Avg shortlist: {metrics.path_b.avg_shortlist_size}</li>
            <li>Avg output: {metrics.path_b.avg_output_count}</li>
            <li>Avg latency: {metrics.path_b.avg_processing_latency_ms} ms</li>
          </ul>
        </div>
      )}

      {matches && (
        <div className="card">
          <h2>Recent matches</h2>
          {matches.items.length === 0 && <p className="muted">No processed items yet.</p>}
          {matches.items.map((item) => (
            <div key={item.item_id} className="debug-row">
              <strong>{item.raw_intent}</strong>
              <span className={`match-pill match-${item.match_status}`}>{item.match_status}</span>
              <p className="muted">
                Shortlist {item.shortlist_size ?? "—"} · {item.processing_latency_ms ?? "—"} ms
              </p>
              {item.matches.map((match) => (
                <p key={match.sku_id}>
                  #{match.rank} {match.sku_id} · {Math.round(match.confidence * 100)}% · {match.availability_status}
                </p>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
