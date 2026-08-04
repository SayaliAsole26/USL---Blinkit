import { CatalogMatchResponse, MatchStatus, UslItemResponse } from "../api/client";
import Icon from "./layout/Icon";

type Props = {
  item: UslItemResponse;
  onEdit: (item: UslItemResponse) => void;
  onDelete: (itemId: string) => void;
  available?: boolean;
};

function formatMatchStatus(status: MatchStatus): string {
  return status.replace(/_/g, " ");
}

export default function UslItemCard({ item, onEdit, onDelete, available = true }: Props) {
  const topMatch: CatalogMatchResponse | undefined = item.catalog_matches[0];

  if (!available) {
    return (
      <div className="flex items-center gap-4 rounded-xl border border-border-subtle bg-surface-gray p-3 opacity-80">
        <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-lg bg-surface-container grayscale">
          {topMatch?.image_url ? (
            <img src={topMatch.image_url} alt="" className="h-full w-full object-contain p-2" />
          ) : (
            <Icon name="inventory_2" className="text-on-surface-variant" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold">{item.raw_intent}</p>
          <p className="text-xs text-on-surface-variant">Unavailable at your location</p>
        </div>
        <button type="button" className="rounded-lg border border-outline-variant bg-surface-container-high px-4 py-1.5 text-xs font-bold text-on-surface-variant">
          Notify Me
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 rounded-xl border border-border-subtle bg-surface-container-lowest p-3 card-shadow">
      <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-lg bg-surface-container-low">
        {topMatch?.image_url ? (
          <img src={topMatch.image_url} alt="" className="h-full w-full object-contain p-2" />
        ) : (
          <Icon name="shopping_bag" className="text-primary" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold">{item.raw_intent}</p>
        <p className="text-xs text-on-surface-variant">
          {topMatch?.product_name ?? item.normalized_name ?? formatMatchStatus(item.match_status)}
        </p>
        {topMatch?.price != null && (
          <div className="mt-1 flex items-center gap-2">
            <span className="text-sm font-bold">₹{topMatch.price}</span>
            {item.match_status === "matched" && (
              <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary">
                {Math.round(topMatch.match_confidence * 100)}% match
              </span>
            )}
          </div>
        )}
        {item.match_status === "processing" && (
          <p className="mt-1 text-xs text-on-surface-variant">Matching catalog SKUs…</p>
        )}
      </div>
      <div className="flex flex-col gap-1">
        <button
          type="button"
          onClick={() => onEdit(item)}
          className="rounded-lg border border-primary px-4 py-1.5 text-sm font-bold text-primary hover:bg-primary/5"
        >
          Edit
        </button>
        <button type="button" onClick={() => onDelete(item.item_id)} className="text-xs text-error">
          Remove
        </button>
      </div>
    </div>
  );
}
