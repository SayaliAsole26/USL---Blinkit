import { formatStatus } from "./StatusFilter";
import { CatalogMatchResponse, MatchStatus, UslItemResponse } from "../api/client";

type Props = {
  item: UslItemResponse;
  onEdit: (item: UslItemResponse) => void;
  onDelete: (itemId: string) => void;
};

function formatMatchStatus(status: MatchStatus): string {
  return status.replace(/_/g, " ");
}

function AvailabilityBadge({ status }: { status: string }) {
  const cls = status === "available" ? "avail-ok" : status === "unknown" ? "avail-unknown" : "avail-bad";
  return <span className={`avail-badge ${cls}`}>{status}</span>;
}

export default function UslItemCard({ item, onEdit, onDelete }: Props) {
  const topMatch: CatalogMatchResponse | undefined = item.catalog_matches[0];

  return (
    <article className="item-card">
      <div className="item-main">
        <h3>{item.raw_intent}</h3>
        {item.normalized_name && item.normalized_name !== item.raw_intent && (
          <p className="subintent">AI: {item.normalized_name}</p>
        )}
        <p className="meta">
          <span className={`status-pill status-${item.status}`}>{formatStatus(item.status)}</span>
          <span className={`match-pill match-${item.match_status}`}>{formatMatchStatus(item.match_status)}</span>
          {item.priority && <span>Priority {item.priority}</span>}
        </p>
        {topMatch && (
          <div className="match-preview">
            <strong>{topMatch.product_name}</strong>
            {topMatch.price != null && <span> · ₹{topMatch.price}</span>}
            <AvailabilityBadge status={topMatch.availability_status} />
            <span className="confidence">{Math.round(topMatch.match_confidence * 100)}% match</span>
          </div>
        )}
        {item.match_status === "processing" && <p className="muted">Matching catalog SKUs…</p>}
        {item.match_status === "unmatched" && <p className="muted">No catalog match yet — item stays on your list.</p>}
      </div>
      <div className="item-actions">
        <button type="button" className="btn-ghost" onClick={() => onEdit(item)}>
          Edit
        </button>
        <button type="button" className="btn-danger" onClick={() => onDelete(item.item_id)}>
          Delete
        </button>
      </div>
    </article>
  );
}
