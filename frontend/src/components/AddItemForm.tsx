import { FormEvent, useState } from "react";

type Props = {
  onAdd: (rawIntent: string, priority?: number) => Promise<void>;
};

export default function AddItemForm({ onAdd }: Props) {
  const [rawIntent, setRawIntent] = useState("");
  const [priority, setPriority] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!rawIntent.trim()) return;
    setLoading(true);
    setError("");
    try {
      await onAdd(rawIntent.trim(), priority === "" ? undefined : priority);
      setRawIntent("");
      setPriority("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="add-form" onSubmit={handleSubmit}>
      <input
        value={rawIntent}
        onChange={(e) => setRawIntent(e.target.value)}
        placeholder='e.g. "AirPods", "Dog Food", "Face Wash"'
        maxLength={500}
        required
      />
      <select value={priority} onChange={(e) => setPriority(e.target.value ? Number(e.target.value) : "")}>
        <option value="">Priority (optional)</option>
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? "Adding…" : "Add to list"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
