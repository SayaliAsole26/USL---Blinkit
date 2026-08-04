import { CheckoutRecommendation } from "../api/client";

type Props = {
  recommendation: CheckoutRecommendation;
  onAction: (action: "added_to_cart" | "saved_for_later" | "dismissed") => void;
  loading: boolean;
};

export default function RecommendationCard({ recommendation, onAction, loading }: Props) {
  return (
    <article className="rec-card">
      <div className="rec-main">
        {recommendation.image_url && (
          <img src={recommendation.image_url} alt={recommendation.product_name} className="rec-image" />
        )}
        <div>
          <span className="rec-type">{recommendation.reason_type.replace(/_/g, " ")}</span>
          <h3>{recommendation.product_name}</h3>
          <p className="rec-reason">{recommendation.reason_text}</p>
          <p className="rec-price">₹{recommendation.price}</p>
        </div>
      </div>
      <div className="rec-actions">
        <button type="button" className="btn-primary" disabled={loading} onClick={() => onAction("added_to_cart")}>
          Add to cart
        </button>
        <button type="button" className="btn-ghost" disabled={loading} onClick={() => onAction("saved_for_later")}>
          Save for later
        </button>
        <button type="button" className="btn-danger" disabled={loading} onClick={() => onAction("dismissed")}>
          Dismiss
        </button>
      </div>
    </article>
  );
}
