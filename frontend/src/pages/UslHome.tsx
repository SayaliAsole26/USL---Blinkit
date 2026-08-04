import { useCallback, useEffect, useMemo, useState } from "react";
import { api, LocationResponse, UslItemResponse } from "../api/client";
import AddItemForm from "../components/AddItemForm";
import EditItemModal from "../components/EditItemModal";
import Icon from "../components/layout/Icon";
import AiPill from "../components/ui/AiPill";
import CompletionScore from "../components/ui/CompletionScore";
import UslItemCard from "../components/UslItemCard";

type Props = {
  location: LocationResponse;
  onContinueShopping?: () => void;
};

type ListFilter = "all" | "available" | "unavailable";

function isAvailable(item: UslItemResponse): boolean {
  const match = item.catalog_matches[0];
  if (!match) return item.match_status !== "matched";
  return match.availability_status === "available" || match.availability_status === "unknown";
}

export default function UslHome({ location, onContinueShopping }: Props) {
  const [filter, setFilter] = useState<ListFilter>("all");
  const [search, setSearch] = useState("");
  const [items, setItems] = useState<UslItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingItem, setEditingItem] = useState<UslItemResponse | null>(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listItems("all");
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load items");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  useEffect(() => {
    const hasProcessing = items.some((item) => item.match_status === "queued" || item.match_status === "processing");
    if (!hasProcessing) return;
    const timer = window.setInterval(() => loadItems(), 3000);
    return () => window.clearInterval(timer);
  }, [items, loadItems]);

  const filtered = useMemo(() => {
    let list = items;
    if (filter === "available") list = list.filter(isAvailable);
    if (filter === "unavailable") list = list.filter((i) => !isAvailable(i));
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((i) => i.raw_intent.toLowerCase().includes(q));
    }
    return list;
  }, [items, filter, search]);

  const availableItems = items.filter(isAvailable);
  const unavailableItems = items.filter((i) => !isAvailable(i));
  const completionScore = items.length === 0 ? 0 : Math.round((availableItems.length / items.length) * 100);

  async function handleAdd(rawIntent: string, priority?: number, eventDate?: string) {
    await api.createItem({
      raw_intent: rawIntent,
      priority,
      event_date: eventDate ? `${eventDate}T00:00:00Z` : undefined,
    });
    await loadItems();
  }

  async function handleDelete(itemId: string) {
    if (!confirm("Remove this item from your Universal Shopping List?")) return;
    await api.deleteItem(itemId);
    await loadItems();
  }

  async function handleWatch(itemId: string) {
    try {
      const result = await api.watchItemAvailability(itemId);
      alert(result.message || "We'll notify you when this item is available.");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not set availability alert.");
    }
  }

  async function handleSave(
    itemId: string,
    updates: {
      raw_intent: string;
      status: UslItemResponse["status"];
      priority?: number;
      event_date?: string | null;
    },
  ) {
    await api.updateItem(itemId, updates);
    await loadItems();
  }

  const chips: { id: ListFilter; label: string; count: number }[] = [
    { id: "all", label: "All", count: items.length },
    { id: "available", label: "Available on Blinkit", count: availableItems.length },
    { id: "unavailable", label: "Not Available", count: unavailableItems.length },
  ];

  return (
    <div className="min-h-screen bg-surface pb-24">
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between bg-surface px-4">
        <div>
          <h1 className="text-lg font-bold text-primary">My Universal List</h1>
          <p className="text-xs text-on-surface-variant">All your needs, at one place</p>
        </div>
        <Icon name="notifications" className="text-primary" />
      </header>

      <main className="space-y-4 px-4 pt-2">
        <div className="relative">
          <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search in your list"
            className="h-11 w-full rounded-xl border-none bg-surface-container-low pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <AiPill />

        <div className="hide-scrollbar flex gap-2 overflow-x-auto">
          {chips.map((chip) => (
            <button
              key={chip.id}
              type="button"
              onClick={() => setFilter(chip.id)}
              className={`flex-shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-all active:scale-95 ${
                filter === chip.id
                  ? "bg-primary font-bold text-on-primary"
                  : "bg-surface-container-high text-on-surface-variant"
              }`}
            >
              {chip.label} ({chip.count})
            </button>
          ))}
        </div>

        <AddItemForm onAdd={handleAdd} />

        {loading && <p className="text-sm text-on-surface-variant">Loading…</p>}
        {error && <p className="text-sm text-error">{error}</p>}

        {!loading && filtered.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-base font-bold">
              {filter === "unavailable" ? "Not Available on Blinkit" : "Available on Blinkit"}
            </h2>
            {filtered.map((item) => (
              <UslItemCard
                key={item.item_id}
                item={item}
                available={isAvailable(item)}
                onEdit={setEditingItem}
                onDelete={handleDelete}
                onWatch={handleWatch}
              />
            ))}
          </section>
        )}

        {!loading && items.length === 0 && (
          <p className="py-8 text-center text-sm text-on-surface-variant">
            No items yet. Add cross-category intents like &quot;AirPods&quot; or &quot;Dog Food&quot;.
          </p>
        )}

        {items.length > 0 && (
          <CompletionScore
            score={completionScore}
            hint="Add a few more items to complete your weekly household shopping goal."
          />
        )}

        {onContinueShopping && items.length > 0 && (
          <button
            type="button"
            onClick={onContinueShopping}
            className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-primary-container text-base font-semibold text-on-primary active:scale-[0.96]"
          >
            Continue to shop
            <Icon name="chevron_right" />
          </button>
        )}

        <p className="text-center text-xs text-on-surface-variant">
          Delivering to {location.city}, {location.state} · {location.pincode}
        </p>
      </main>

      <EditItemModal item={editingItem} onClose={() => setEditingItem(null)} onSave={handleSave} />
    </div>
  );
}
