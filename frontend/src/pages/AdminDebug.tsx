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
    <div className="min-h-screen bg-surface p-4 pb-10">
      <div className="mb-4">
        <span className="rounded-full bg-ai-surface px-3 py-1 text-[11px] font-bold text-ai-text">Admin debug</span>
        <h1 className="mt-2 text-xl font-bold">Path A match quality</h1>
        <p className="text-sm text-on-surface-variant">Review catalog matches and pipeline metrics.</p>
      </div>

      {error && <p className="mb-4 text-sm text-error">{error}</p>}

      {metrics && (
        <div className="mb-4 rounded-xl border border-border-subtle bg-white p-4 card-shadow">
          <h2 className="mb-2 font-bold">Pipeline metrics</h2>
          <h3 className="text-sm font-semibold text-primary">Path A (ingest)</h3>
          <ul className="mb-3 list-inside list-disc text-sm text-on-surface-variant">
            <li>Runs: {metrics.path_a.runs}</li>
            <li>Avg shortlist: {metrics.path_a.avg_shortlist_size}</li>
            <li>Max LLM candidates: {metrics.path_a.max_llm_candidate_size}</li>
          </ul>
          <h3 className="text-sm font-semibold text-primary">Path B (checkout)</h3>
          <ul className="list-inside list-disc text-sm text-on-surface-variant">
            <li>Runs: {metrics.path_b.runs}</li>
            <li>Avg shortlist: {metrics.path_b.avg_shortlist_size}</li>
            <li>Avg output: {metrics.path_b.avg_output_count}</li>
            <li>Avg latency: {metrics.path_b.avg_processing_latency_ms} ms</li>
          </ul>
        </div>
      )}

      {matches && (
        <div className="rounded-xl border border-border-subtle bg-white p-4 card-shadow">
          <h2 className="mb-3 font-bold">Recent matches</h2>
          {matches.items.length === 0 && <p className="text-sm text-on-surface-variant">No processed items yet.</p>}
          {matches.items.map((item) => (
            <div key={item.item_id} className="border-b border-border-subtle py-3 last:border-0">
              <strong className="text-sm">{item.raw_intent}</strong>
              <span className="ml-2 rounded-full bg-surface-gray px-2 py-0.5 text-xs capitalize">{item.match_status}</span>
              <p className="text-xs text-on-surface-variant">
                Shortlist {item.shortlist_size ?? "—"} · {item.processing_latency_ms ?? "—"} ms
              </p>
              {item.matches.map((match) => (
                <p key={match.sku_id} className="text-xs text-on-surface-variant">
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
