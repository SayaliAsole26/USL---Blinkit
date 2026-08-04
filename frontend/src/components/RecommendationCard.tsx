import { CheckoutRecommendation } from "../api/client";
import Icon from "./layout/Icon";
import ProductImage from "./ui/ProductImage";

type Props = {
  recommendation: CheckoutRecommendation;
  onAction: (action: "added_to_cart" | "saved_for_later" | "dismissed") => void;
  loading: boolean;
};

const REASON_ICONS: Record<string, string> = {
  weather_context: "wb_sunny",
  seasonal_context: "eco",
  event_based: "event",
  replenishment_reminder: "schedule",
  memory_reminder: "history",
  cross_category_discovery: "auto_awesome",
  shopping_completion: "shopping_cart",
};

export default function RecommendationCard({ recommendation, onAction, loading }: Props) {
  const iconName = REASON_ICONS[recommendation.reason_type] ?? "auto_awesome";

  return (
    <article className="flex gap-4 rounded-xl border border-border-subtle bg-surface-container-lowest p-3 transition-all active:scale-[0.98] card-shadow">
      <div className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg bg-surface-container-low">
        <ProductImage
          product={{
            sku_id: recommendation.sku_id,
            product_name: recommendation.product_name,
            category: recommendation.reason_type,
            image_url: recommendation.image_url,
          }}
          className="h-full w-full object-cover"
        />
      </div>
      <div className="flex flex-1 flex-col justify-between">
        <div>
          <div className="mb-1 inline-flex items-center gap-1 rounded-full bg-ai-surface px-2 py-0.5 text-ai-text">
            <Icon name={iconName} filled size={12} />
            <span className="text-[11px] font-bold capitalize">{recommendation.reason_type.replace(/_/g, " ")}</span>
          </div>
          <h3 className="text-sm font-medium">{recommendation.product_name}</h3>
          <p className="text-xs text-on-surface-variant line-clamp-2">{recommendation.reason_text}</p>
        </div>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-sm font-bold">₹{recommendation.price}</span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() => onAction("added_to_cart")}
              className="flex h-9 items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-on-primary active:scale-95 disabled:opacity-50"
            >
              + Add
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => onAction("dismissed")}
              className="rounded-lg px-2 text-on-surface-variant active:scale-95 disabled:opacity-50"
              aria-label="Dismiss"
            >
              <Icon name="close" size={18} />
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
