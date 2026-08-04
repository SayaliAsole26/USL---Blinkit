import { useCallback, useEffect, useMemo, useState } from "react";
import { api, CatalogProduct, CheckoutRecommendation, LocationResponse } from "../api/client";
import Icon from "../components/layout/Icon";
import RecommendationCard from "../components/RecommendationCard";
import CompletionScore from "../components/ui/CompletionScore";

type Props = {
  location: LocationResponse;
  onBack: () => void;
  onOrderPlaced: (message: string) => void;
};

export default function CheckoutPage({ location, onBack, onOrderPlaced }: Props) {
  const [cartItems, setCartItems] = useState<Array<{ sku_id: string; quantity: number }>>([]);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [recommendations, setRecommendations] = useState<CheckoutRecommendation[]>([]);
  const [checkoutSessionId, setCheckoutSessionId] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState("");
  const [recError, setRecError] = useState("");

  const productBySku = useMemo(() => new Map(products.map((p) => [p.sku_id, p])), [products]);

  const loadCheckout = useCallback(async () => {
    setLoading(true);
    setError("");
    setRecError("");
    try {
      const [cart, catalog] = await Promise.all([
        api.getCart(),
        api.listCatalogProducts({ pincode: location.pincode }),
      ]);
      setCartItems(cart.items);
      setProducts(catalog.products);

      try {
        const cartSkus = cart.items.map((i) => i.sku_id).join(",");
        const data = await api.getCheckoutRecommendations(cartSkus || undefined);
        setCheckoutSessionId(data.checkout_session_id);
        setRecommendations(data.recommendations);
      } catch (err) {
        setRecommendations([]);
        setRecError(err instanceof Error ? err.message : "Recommendations unavailable");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load checkout");
    } finally {
      setLoading(false);
    }
  }, [location.pincode]);

  useEffect(() => {
    loadCheckout();
  }, [loadCheckout]);

  const cartTotal = cartItems.reduce((sum, item) => {
    const product = productBySku.get(item.sku_id);
    return sum + (product?.price ?? 0) * item.quantity;
  }, 0);

  const itemCount = cartItems.reduce((s, i) => s + i.quantity, 0);
  const completionScore = Math.min(95, 60 + recommendations.length * 8 + itemCount * 3);

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
      setRecError(err instanceof Error ? err.message : "Action failed");
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
    setPlacing(true);
    try {
      const result = await api.completeOrder(`ord_${Date.now()}`, skuIds);
      onOrderPlaced(`Order placed — ${result.usl_items_marked_purchased} USL item(s) synced.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Order failed");
    } finally {
      setPlacing(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface pb-36">
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between bg-surface px-4">
        <div className="flex items-center gap-3">
          <button type="button" onClick={onBack} className="rounded-full p-2 active:scale-95">
            <Icon name="arrow_back" />
          </button>
          <div>
            <h1 className="text-lg font-bold">My Cart ({itemCount} items)</h1>
            <p className="text-xs text-on-surface-variant">
              Delivering to {location.pincode} - {location.city}, {location.state}
            </p>
          </div>
        </div>
        <span className="text-lg font-bold text-primary">₹{cartTotal.toFixed(0)}</span>
      </header>

      <main className="space-y-4 px-4 pt-4">
        <CompletionScore
          score={completionScore}
          hint="Add a few more items to complete your shopping based on your recurring needs."
        />

        {cartItems.length > 0 && (
          <section className="rounded-xl border border-border-subtle bg-surface-container-low p-4 opacity-90">
            <h2 className="mb-3 text-sm font-bold">Cart items</h2>
            <ul className="space-y-2 text-sm">
              {cartItems.map((item) => {
                const product = productBySku.get(item.sku_id);
                return (
                  <li key={item.sku_id} className="flex justify-between">
                    <span>{product?.product_name ?? item.sku_id} × {item.quantity}</span>
                    <span className="font-bold">₹{((product?.price ?? 0) * item.quantity).toFixed(0)}</span>
                  </li>
                );
              })}
            </ul>
            <div className="mt-3 flex justify-between border-t border-border-subtle pt-3 text-sm">
              <span>Delivery Fee</span>
              <span>
                <span className="text-on-surface-variant line-through">₹25</span>{" "}
                <span className="font-bold text-primary">FREE</span>
              </span>
            </div>
          </section>
        )}

        <div className="flex items-center gap-2 pt-2">
          <Icon name="auto_awesome" filled className="text-ai-text" />
          <h2 className="text-base font-bold">You may need these too</h2>
        </div>

        {loading && <p className="text-sm text-on-surface-variant">Loading recommendations…</p>}
        {error && <p className="text-sm text-error">{error}</p>}
        {recError && !loading && (
          <div className="space-y-2 rounded-xl bg-error-container/30 p-3">
            <p className="text-sm text-error">{recError}</p>
            <button
              type="button"
              onClick={loadCheckout}
              className="text-sm font-semibold text-primary"
            >
              Retry recommendations
            </button>
          </div>
        )}
        {!loading && !recError && recommendations.length === 0 && (
          <p className="rounded-xl bg-surface-container-low p-4 text-sm text-on-surface-variant">
            No checkout recommendations right now — add USL items with catalog matches.
          </p>
        )}
        <div className="space-y-3">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.recommendation_id}
              recommendation={rec}
              loading={actionLoading}
              onAction={(action) => handleAction(rec, action)}
            />
          ))}
        </div>
      </main>

      <footer className="fixed bottom-0 left-0 z-50 w-full border-t border-border-subtle bg-surface px-4 py-3 pb-8">
        <div className="mx-auto max-w-md">
          <button
            type="button"
            onClick={placeOrder}
            disabled={cartItems.length === 0 || placing}
            className="flex h-14 w-full items-center justify-between rounded-xl bg-primary-container px-6 text-on-primary shadow-lg transition-transform active:scale-[0.98] disabled:opacity-50"
          >
            <div className="flex flex-col items-start">
              <span className="text-lg font-bold">₹{cartTotal.toFixed(0)}</span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-on-primary/80">Total Bill</span>
            </div>
            <div className="flex items-center gap-1 text-base font-semibold">
              {placing ? "Placing…" : "Place Order"}
              <Icon name="chevron_right" />
            </div>
          </button>
        </div>
      </footer>
    </div>
  );
}
