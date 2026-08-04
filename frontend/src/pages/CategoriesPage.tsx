import { useEffect, useState } from "react";
import { api, LocationResponse } from "../api/client";
import LocationBanner from "../components/layout/LocationBanner";

const CATEGORY_ICONS: Record<string, string> = {
  Groceries: "🥬",
  "Personal Care": "✨",
  Electronics: "🔌",
  "Pet Supplies": "🐾",
  "Home Essentials": "🏠",
  "Health & Nutrition": "💪",
  Gifting: "🎁",
};

type Props = {
  location: LocationResponse;
  onChangeLocation: () => void;
  onSelectCategory: (category: string) => void;
};

export default function CategoriesPage({ location, onChangeLocation, onSelectCategory }: Props) {
  const [categories, setCategories] = useState<string[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listCatalogProducts({ pincode: location.pincode })
      .then((catalog) => {
        const byCat: Record<string, number> = {};
        for (const p of catalog.products) {
          byCat[p.category] = (byCat[p.category] ?? 0) + 1;
        }
        setCounts(byCat);
        setCategories(Object.keys(byCat).sort());
      })
      .finally(() => setLoading(false));
  }, [location.pincode]);

  return (
    <div className="min-h-screen bg-surface pb-20">
      <header className="sticky top-0 z-40 border-b border-border-subtle bg-surface px-4 py-3">
        <h1 className="mb-3 text-lg font-bold">Categories</h1>
        <LocationBanner location={location} onChangeLocation={onChangeLocation} compact />
      </header>

      <main className="p-4">
        {loading && <p className="text-sm text-on-surface-variant">Loading categories…</p>}
        <div className="grid grid-cols-2 gap-3">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => onSelectCategory(cat)}
              className="flex flex-col items-start gap-2 rounded-xl border border-border-subtle bg-surface-container-low p-4 text-left active:scale-[0.98]"
            >
              <span className="text-3xl">{CATEGORY_ICONS[cat] ?? "📦"}</span>
              <span className="font-semibold">{cat}</span>
              <span className="text-xs text-on-surface-variant">{counts[cat] ?? 0} items near you</span>
            </button>
          ))}
        </div>
        {!loading && categories.length === 0 && (
          <p className="rounded-xl bg-surface-container-low p-4 text-sm text-on-surface-variant">
            No categories available for pincode {location.pincode}. Try changing your location.
          </p>
        )}
      </main>
    </div>
  );
}
