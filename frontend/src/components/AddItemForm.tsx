import { FormEvent, useState } from "react";
import Icon from "./layout/Icon";

type Props = {
  onAdd: (rawIntent: string, priority?: number, eventDate?: string) => Promise<void>;
};

const EXAMPLES = [
  { label: "Face Wash", category: "Skincare & Hygiene" },
  { label: "Sunscreen", category: "Summer Essentials" },
  { label: "Dog Food", category: "Pet Supplies" },
  { label: "AirPods", category: "Electronics" },
];

function looksLikeGiftIntent(text: string): boolean {
  const lower = text.toLowerCase();
  return /gift|birthday|anniversary|hamper|celebration|party|wedding/.test(lower);
}

export default function AddItemForm({ onAdd }: Props) {
  const [rawIntent, setRawIntent] = useState("");
  const [priority, setPriority] = useState<number | "">("");
  const [eventDate, setEventDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const showEventDate = looksLikeGiftIntent(rawIntent);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!rawIntent.trim()) return;
    setLoading(true);
    setError("");
    try {
      await onAdd(
        rawIntent.trim(),
        priority === "" ? undefined : priority,
        eventDate || undefined,
      );
      setRawIntent("");
      setPriority("");
      setEventDate("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setLoading(false);
    }
  }

  async function addExample(label: string) {
    setLoading(true);
    setError("");
    try {
      await onAdd(label);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="relative">
          <Icon name="add" className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant" />
          <input
            value={rawIntent}
            onChange={(e) => setRawIntent(e.target.value)}
            placeholder="+ Add anything..."
            maxLength={500}
            className="h-14 w-full rounded-xl border-none bg-surface pl-12 pr-4 text-sm placeholder:text-on-surface-variant/60 card-shadow focus:outline-none focus:ring-2 focus:ring-primary-container/30"
          />
        </div>
        <p className="px-1 text-xs italic text-on-surface-variant">Add from anywhere — apps, photos, or handwritten lists.</p>

        <div className="flex flex-wrap gap-2">
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value ? Number(e.target.value) : "")}
            className="rounded-lg border border-border-subtle bg-surface px-3 py-2 text-sm"
          >
            <option value="">Priority (optional)</option>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                Priority {n}
              </option>
            ))}
          </select>
          {showEventDate && (
            <input
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              min={new Date().toISOString().slice(0, 10)}
              className="rounded-lg border border-border-subtle bg-surface px-3 py-2 text-sm"
            />
          )}
          <button
            type="submit"
            disabled={loading || !rawIntent.trim()}
            className="rounded-lg bg-primary-container px-5 py-2 text-sm font-semibold text-on-primary disabled:opacity-50"
          >
            {loading ? "Adding…" : "Add to list"}
          </button>
        </div>
        {error && <p className="text-sm text-error">{error}</p>}
      </form>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-on-surface-variant">Examples — Add from anywhere</h2>
          <span className="flex items-center gap-1 rounded-full bg-ai-surface px-2 py-1 text-[11px] font-bold text-ai-text">
            <Icon name="auto_awesome" size={12} />
            Smart Match
          </span>
        </div>
        <div className="divide-y divide-border-subtle overflow-hidden rounded-2xl bg-surface card-shadow">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              type="button"
              disabled={loading}
              onClick={() => addExample(ex.label)}
              className="flex w-full items-center justify-between p-4 transition-colors hover:bg-surface-container-low active:scale-[0.98]"
            >
              <div className="text-left">
                <p className="text-sm font-medium">{ex.label}</p>
                <p className="text-xs text-on-surface-variant">{ex.category}</p>
              </div>
              <Icon name="chevron_right" className="text-on-surface-variant opacity-40" />
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
