import { useCallback, useEffect, useState } from "react";
import { api, CheckoutRecommendation, LocationResponse } from "../api/client";
import RecommendationCard from "../components/RecommendationCard";

type Props = {
  location: LocationResponse;
  onBack: () => void;
};

export default function CheckoutPage({ location, onBack }: Props) {
  const [cartItems, setCartItems] = useState<Array<{ sku_id: string; quantity: number }>>([]);
  const [recommendations, setRecommendations] = useState<CheckoutRecommendation[]>([]);
  const [checkoutSessionId, setCheckoutSessionId] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [orderMessage, setOrderMessage] = useState("");

  const loadCheckout = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const cart = await api.getCart();
      setCartItems(cart.items);
      const cartSkus = cart.items.map((i) => i.sku_id).join(",");
      const data = await api.getCheckoutRecommendations(cartSkus || undefined);
      setCheckoutSessionId(data.checkout_session_id);
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load checkout recommendations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCheckout();
  }, [loadCheckout]);

  async function addGroceryToCart() {
    await api.addCartItem("sku_milk_001");
    await loadCheckout();
  }

  async function handleAction(rec: CheckoutRecommendation, action: "added_to_cart" | "saved_for_later" | "dismissed") {
    setActionLoading(true);
    try {
      await api.recommendationAction(rec.recommendation_id, action, checkoutSessionId);
      if (action === "added_to_cart") {
        await loadCheckout();
      } else {
        setRecommendations((prev) => prev.filter((r) => r.recommendation_id !== rec.recommendation_id));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionLoading(false);
    }
  }

  async function placeOrder() {
    const skuIds = cartItems.map((i) => i.sku_id);
    if (skuIds.length === 0) {
      setError("Add items to cart before placing order");
      return;
    }
    const result = await api.completeOrder(`ord_${Date.now()}`, skuIds);
    setOrderMessage(`Order placed — ${result.usl_items_marked_purchased} USL item(s) synced.`);
    setCartItems([]);
    setRecommendations([]);
  }

  return (
    <div className="page">
      <header className="hero compact">
        <button type="button" className="btn-ghost back-btn" onClick={onBack}>
          ← Back to list
        </button>
        <span className="badge">Checkout only</span>
        <h1>Checkout</h1>
        <p className="location-line">
          Delivering to <strong>{location.city}</strong> · {location.pincode}
        </p>
        <p className="hint">USL recommendations appear here only — not during browse or search.</p>
      </header>

      <div className="card">
        <h2>Your cart</h2>
        {cartItems.length === 0 && <p className="muted">Cart is empty. Add groceries to simulate checkout.</p>}
        <ul className="cart-list">
          {cartItems.map((item) => (
            <li key={item.sku_id}>
              {item.sku_id} × {item.quantity}
            </li>
          ))}
        </ul>
        <div className="cart-actions">
          <button type="button" className="btn-ghost" onClick={addGroceryToCart}>
            Add Amul Milk (groceries)
          </button>
          <button type="button" className="btn-primary" onClick={placeOrder} disabled={cartItems.length === 0}>
            Place order
          </button>
        </div>
        {orderMessage && <p className="success">{orderMessage}</p>}
      </div>

      <div className="card">
        <h2>From your Universal Shopping List</h2>
        {loading && <p className="muted">Loading recommendations…</p>}
        {error && <p className="error">{error}</p>}
        {!loading && !error && recommendations.length === 0 && (
          <p className="empty-state">No checkout recommendations right now — add USL items with catalog matches.</p>
        )}
        <div className="rec-list">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.recommendation_id}
              recommendation={rec}
              loading={actionLoading}
              onAction={(action) => handleAction(rec, action)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
