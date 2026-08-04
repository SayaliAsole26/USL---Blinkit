import { useCallback, useEffect, useState } from "react";
import { api, LocationResponse, StatusFilter, UslItemResponse } from "../api/client";
import AddItemForm from "../components/AddItemForm";
import EditItemModal from "../components/EditItemModal";
import StatusFilterBar from "../components/StatusFilter";
import UslItemCard from "../components/UslItemCard";

type Props = {
  location: LocationResponse;
  checkoutEnabled?: boolean;
  onGoToCheckout?: () => void;
};

export default function UslHome({ location, checkoutEnabled = false, onGoToCheckout }: Props) {
  const [filter, setFilter] = useState<StatusFilter>("pending");
  const [items, setItems] = useState<UslItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingItem, setEditingItem] = useState<UslItemResponse | null>(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listItems(filter);
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load items");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  useEffect(() => {
    const hasProcessing = items.some((item) => item.match_status === "queued" || item.match_status === "processing");
    if (!hasProcessing) return;
    const timer = window.setInterval(() => loadItems(), 3000);
    return () => window.clearInterval(timer);
  }, [items, loadItems]);

  async function handleAdd(rawIntent: string, priority?: number) {
    await api.createItem({ raw_intent: rawIntent, priority });
    await loadItems();
  }

  async function handleDelete(itemId: string) {
    if (!confirm("Remove this item from your Universal Shopping List?")) return;
    await api.deleteItem(itemId);
    await loadItems();
  }

  async function handleSave(
    itemId: string,
    updates: { raw_intent: string; status: UslItemResponse["status"]; priority?: number },
  ) {
    await api.updateItem(itemId, updates);
    await loadItems();
  }

  return (
    <div className="page">
      <header className="hero compact">
        <span className="badge">Universal Shopping List</span>
        <h1>Your saved items</h1>
        <p className="location-line">
          Delivering to <strong>{location.city}</strong>, {location.state} · {location.pincode}
        </p>
        <p className="hint">Add anything you plan to buy — groceries, electronics, pet supplies, and more.</p>
        {checkoutEnabled && onGoToCheckout && (
          <button type="button" className="btn-primary checkout-cta" onClick={onGoToCheckout}>
            Go to checkout
          </button>
        )}
      </header>

      <div className="card">
        <h2>Add item</h2>
        <AddItemForm onAdd={handleAdd} />
      </div>

      <div className="card">
        <div className="list-header">
          <h2>My list</h2>
          <StatusFilterBar value={filter} onChange={setFilter} />
        </div>

        {loading && <p className="muted">Loading…</p>}
        {error && <p className="error">{error}</p>}
        {!loading && !error && items.length === 0 && (
          <p className="empty-state">No items yet. Add cross-category intents like &quot;AirPods&quot; or &quot;Dog Food&quot;.</p>
        )}
        <div className="item-list">
          {items.map((item) => (
            <UslItemCard key={item.item_id} item={item} onEdit={setEditingItem} onDelete={handleDelete} />
          ))}
        </div>
      </div>

      <EditItemModal item={editingItem} onClose={() => setEditingItem(null)} onSave={handleSave} />
    </div>
  );
}
