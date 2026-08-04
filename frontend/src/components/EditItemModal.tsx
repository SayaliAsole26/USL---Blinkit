import { FormEvent, useEffect, useState } from "react";
import { UslItemResponse, UslItemStatus } from "../api/client";
import Icon from "./layout/Icon";

type Props = {
  item: UslItemResponse | null;
  onClose: () => void;
  onSave: (
    itemId: string,
    updates: { raw_intent: string; status: UslItemStatus; priority?: number; event_date?: string | null },
  ) => Promise<void>;
};

const STATUSES: UslItemStatus[] = ["pending", "saved_for_later", "dismissed", "purchased"];

function toDateInputValue(iso: string | null): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}

export default function EditItemModal({ item, onClose, onSave }: Props) {
  const [rawIntent, setRawIntent] = useState("");
  const [status, setStatus] = useState<UslItemStatus>("pending");
  const [priority, setPriority] = useState<number | "">("");
  const [eventDate, setEventDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (item) {
      setRawIntent(item.raw_intent);
      setStatus(item.status);
      setPriority(item.priority ?? "");
      setEventDate(toDateInputValue(item.event_date));
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
        event_date: eventDate ? `${eventDate}T00:00:00Z` : null,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update item");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center bg-black/40 p-4 sm:items-center" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-t-3xl bg-surface p-6 sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold">Edit item</h2>
          <button type="button" onClick={onClose} aria-label="Close">
            <Icon name="close" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-semibold">
            What do you want to buy?
            <input
              value={rawIntent}
              onChange={(e) => setRawIntent(e.target.value)}
              required
              maxLength={500}
              className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm"
            />
          </label>
          <label className="block text-sm font-semibold">
            Status
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as UslItemStatus)}
              className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-semibold">
            Priority
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value ? Number(e.target.value) : "")}
              className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm"
            >
              <option value="">None</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-semibold">
            Event date (optional)
            <input
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm"
            />
          </label>
          {error && <p className="text-sm text-error">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-sm font-medium text-on-surface-variant">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-primary-container px-5 py-2 text-sm font-semibold text-on-primary disabled:opacity-50"
            >
              {loading ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
