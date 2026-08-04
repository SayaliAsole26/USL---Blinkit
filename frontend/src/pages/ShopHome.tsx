import { useCallback, useEffect, useMemo, useState } from "react";
import { api, CatalogProduct, LocationResponse } from "../api/client";
import Icon from "../components/layout/Icon";
import LocationBanner from "../components/layout/LocationBanner";
import CompletionScore from "../components/ui/CompletionScore";
import ProductImage from "../components/ui/ProductImage";
import { useDebouncedValue } from "../hooks/useDebouncedValue";

type Props = {
  location: LocationResponse;
  checkoutEnabled?: boolean;
  uslAvailablePct?: number;
  initialCategory?: string;
  onCategoryApplied?: () => void;
  onGoToCheckout: () => void;
  onGoToUsl: () => void;
  onChangeLocation: () => void;
};

const CATEGORY_ICONS: Record<string, string> = {
  Groceries: "🥬",
  "Personal Care": "✨",
  Electronics: "🔌",
  "Pet Supplies": "🐾",
  "Home Essentials": "🏠",
  "Health & Nutrition": "💪",
  Gifting: "🎁",
};

export default function ShopHome({
  location,
  checkoutEnabled = false,
  uslAvailablePct = 0,
  initialCategory = "all",
  onCategoryApplied,
  onGoToCheckout,
  onGoToUsl,
  onChangeLocation,
}: Props) {
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [allCategories, setAllCategories] = useState<string[]>([]);
  const [cartItems, setCartItems] = useState<Array<{ sku_id: string; quantity: number }>>([]);
  const [category, setCategory] = useState<string>(initialCategory);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [loading, setLoading] = useState(true);
  const [addingSku, setAddingSku] = useState<string | null>(null);
  const [addedSkus, setAddedSkus] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialCategory !== "all") {
      setCategory(initialCategory);
      onCategoryApplied?.();
    }
  }, [initialCategory, onCategoryApplied]);

  const loadShop = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [catalog, cart] = await Promise.all([
        api.listCatalogProducts({
          category: category === "all" ? undefined : category,
          q: debouncedSearch.trim() || undefined,
          pincode: location.pincode,
        }),
        api.getCart(),
      ]);
      setProducts(catalog.products);
      setCartItems(cart.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load shop");
    } finally {
      setLoading(false);
    }
  }, [category, debouncedSearch, location.pincode]);

  useEffect(() => {
    api.listCatalogProducts({ pincode: location.pincode }).then((catalog) => {
      setAllCategories(Array.from(new Set(catalog.products.map((p) => p.category))).sort());
    });
  }, [location.pincode]);

  useEffect(() => {
    loadShop();
  }, [loadShop]);

  const productBySku = useMemo(() => new Map(products.map((p) => [p.sku_id, p])), [products]);
  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cartItems.reduce((sum, item) => {
    const product = productBySku.get(item.sku_id);
    return sum + (product?.price ?? 0) * item.quantity;
  }, 0);

  async function handleAddToCart(skuId: string) {
    setAddingSku(skuId);
    setError("");
    try {
      await api.addCartItem(skuId);
      const cart = await api.getCart();
      setCartItems(cart.items);
      setAddedSkus((prev) => new Set(prev).add(skuId));
      setTimeout(() => setAddedSkus((prev) => { const n = new Set(prev); n.delete(skuId); return n; }), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setAddingSku(null);
    }
  }

  const categories = ["all", ...allCategories];

  return (
    <div className="min-h-screen bg-surface pb-28">
      <header className="sticky top-0 z-40 bg-brand-yellow transition-shadow">
        <div className="flex flex-col gap-3 px-4 pb-3 pt-4">
          <div className="flex items-center justify-between">
            <LocationBanner location={location} onChangeLocation={onChangeLocation} />
            <button type="button" className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 backdrop-blur-md">
              <Icon name="notifications" />
            </button>
          </div>
          <div className="relative">
            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search 'milk, bread, chips'"
              className="h-12 w-full rounded-xl border-none bg-white pl-10 pr-4 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </div>
      </header>

      <main className="space-y-6">
        <div className="px-4 pt-4">
          <div className="flex items-center justify-between rounded-xl border border-ai-text/10 bg-ai-surface p-4 card-shadow">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-sm">✨</div>
              <div>
                <h3 className="text-base font-bold text-ai-text">My Universal List</h3>
                <p className="text-xs text-ai-text/70">
                  {uslAvailablePct > 0 ? `${uslAvailablePct}% of items available nearby` : "Save items you plan to buy"}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onGoToUsl}
              className="flex items-center gap-1 rounded-lg bg-ai-text px-4 py-2 text-sm font-semibold text-white active:scale-95"
            >
              View
              <Icon name="chevron_right" size={18} />
            </button>
          </div>
        </div>

        <section className="px-4">
          <div className="grid grid-cols-5 gap-2">
            {categories.slice(0, 5).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className="flex flex-col items-center gap-2 active:scale-90"
              >
                <div
                  className={`flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-white shadow-sm ${
                    category === cat ? "ring-2 ring-primary" : ""
                  }`}
                >
                  {cat === "all" ? (
                    <Icon name="grid_view" filled className="text-2xl text-primary" />
                  ) : (
                    <span className="text-xl">{CATEGORY_ICONS[cat] ?? "📦"}</span>
                  )}
                </div>
                <span className="text-[11px] font-bold">{cat === "all" ? "All" : cat.split(" ")[0]}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="relative mx-4 h-36 overflow-hidden rounded-2xl bg-gradient-to-r from-blue-500 to-blue-400">
          <div className="relative z-10 flex h-full flex-col justify-center gap-1 p-6">
            <h2 className="text-2xl font-bold uppercase leading-tight tracking-tight text-white">
              Monsoon
              <br />
              Essentials
            </h2>
            <span className="mt-2 inline-block w-fit rounded-full bg-white px-3 py-1 text-[11px] font-bold text-blue-600">
              Up to 30% OFF
            </span>
          </div>
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between px-4">
            <h2 className="text-base font-bold">
              {debouncedSearch.trim() ? `Results for "${debouncedSearch.trim()}"` : "Bestsellers"}
            </h2>
            <span className="text-xs text-on-surface-variant">{location.city}</span>
          </div>
          {loading && <p className="px-4 text-sm text-on-surface-variant">Loading products…</p>}
          {error && <p className="px-4 text-sm text-error">{error}</p>}
          {!loading && products.length === 0 && (
            <p className="px-4 text-sm text-on-surface-variant">
              No products found{debouncedSearch.trim() ? ` for "${debouncedSearch.trim()}"` : ""} at pincode {location.pincode}.
            </p>
          )}
          <div className="hide-scrollbar flex gap-4 overflow-x-auto px-4 pb-2">
            {products.map((product) => {
              const inCart = cartItems.some((c) => c.sku_id === product.sku_id);
              const justAdded = addedSkus.has(product.sku_id);
              return (
                <div key={product.sku_id} className="flex min-w-[140px] flex-col gap-2">
                  <div className="relative flex aspect-square items-center justify-center overflow-hidden rounded-xl border border-border-subtle bg-white p-2">
                    <ProductImage product={product} />
                  </div>
                  <div className="space-y-0.5">
                    <p className="truncate text-sm font-medium">{product.product_name}</p>
                    <p className="text-xs text-on-surface-variant">{product.category}</p>
                    <div className="mt-1 flex items-center justify-between">
                      <span className="text-sm font-bold">₹{product.price}</span>
                      <button
                        type="button"
                        disabled={addingSku === product.sku_id}
                        onClick={() => handleAddToCart(product.sku_id)}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all active:scale-90 ${
                          inCart || justAdded
                            ? "border-primary bg-primary text-white"
                            : "border-primary text-primary hover:bg-primary hover:text-white"
                        }`}
                      >
                        {justAdded ? "ADDED" : inCart ? "ADD +" : "ADD"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="px-4">
          <CompletionScore
            variant="primary"
            score={uslAvailablePct || 40}
            hint="You usually buy groceries every week. Add a few more items to finish your list."
          />
        </section>
      </main>

      {cartCount > 0 && (
        <div className="fixed bottom-16 left-0 z-50 w-full px-4">
          <div className="mx-auto flex max-w-md items-center justify-between rounded-2xl bg-on-surface px-4 py-3 text-white shadow-xl">
            <div>
              <strong className="text-sm">
                {cartCount} item{cartCount === 1 ? "" : "s"}
              </strong>
              <span className="text-sm text-white/70"> · ₹{cartTotal.toFixed(0)}</span>
            </div>
            {checkoutEnabled ? (
              <button
                type="button"
                onClick={onGoToCheckout}
                className="flex items-center gap-1 rounded-xl bg-primary-container px-4 py-2.5 text-sm font-semibold text-on-primary active:scale-95"
              >
                Go to checkout
                <Icon name="chevron_right" size={18} />
              </button>
            ) : (
              <span className="text-xs text-white/60">Checkout unavailable</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
