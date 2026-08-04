import { FormEvent, useEffect, useState } from "react";
import { UslItemResponse, UslItemStatus } from "../api/client";

type Props = {
  item: UslItemResponse | null;
  onClose: () => void;
  onSave: (itemId: string, updates: { raw_intent: string; status: UslItemStatus; priority?: number }) => Promise<void>;
};

const STATUSES: UslItemStatus[] = ["pending", "saved_for_later", "dismissed", "purchased"];

export default function EditItemModal({ item, onClose, onSave }: Props) {
  const [rawIntent, setRawIntent] = useState("");
  const [status, setStatus] = useState<UslItemStatus>("pending");
  const [priority, setPriority] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (item) {
      setRawIntent(item.raw_intent);
      setStatus(item.status);
      setPriority(item.priority ?? "");
    }
  }, [item]);

  if (!item) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await onSave(item!.item_id, {
        raw_intent: rawIntent.trim(),
        status,
        priority: priority === "" ? undefined : priority,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update item");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal card" onClick={(e) => e.stopPropagation()}>
        <h2>Edit item</h2>
        <form onSubmit={handleSubmit}>
          <label>
            What do you want to buy?
            <input value={rawIntent} onChange={(e) => setRawIntent(e.target.value)} required maxLength={500} />
          </label>
          <label>
            Status
            <select value={status} onChange={(e) => setStatus(e.target.value as UslItemStatus)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Priority
            <select value={priority} onChange={(e) => setPriority(e.target.value ? Number(e.target.value) : "")}>
              <option value="">None</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          {error && <p className="error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
