import { FormEvent, useState } from "react";
import { api } from "../api/client";
import Icon from "../components/layout/Icon";

type Props = {
  onComplete: () => void;
  onBack?: () => void;
};

export default function Onboarding({ onComplete, onBack }: Props) {
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [pincode, setPincode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.setLocation({ city, state, pincode });
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-gray">
      <header className="sticky top-0 z-40 flex h-14 items-center gap-3 bg-surface px-4">
        {onBack && (
          <button type="button" onClick={onBack} className="active-scale flex h-10 w-10 items-center justify-center rounded-full">
            <Icon name="arrow_back" className="text-primary" />
          </button>
        )}
        <div>
          <h1 className="text-lg font-bold text-primary">Set delivery location</h1>
          <p className="text-xs text-on-surface-variant">We use this to check product availability</p>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="mx-4 mt-6 space-y-4 rounded-2xl bg-surface p-5 card-shadow">
        <label className="block text-sm font-semibold">
          City
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Bangalore"
            required
            className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </label>
        <label className="block text-sm font-semibold">
          State
          <input
            value={state}
            onChange={(e) => setState(e.target.value)}
            placeholder="Karnataka"
            required
            className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </label>
        <label className="block text-sm font-semibold">
          Pincode
          <input
            value={pincode}
            onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="560001"
            inputMode="numeric"
            pattern="\d{6}"
            required
            className="mt-1 w-full rounded-xl border border-border-subtle px-3 py-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </label>
        {error && <p className="text-sm text-error">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="h-12 w-full rounded-xl bg-primary-container text-base font-semibold text-on-primary transition-all active:scale-[0.96] disabled:opacity-60"
        >
          {loading ? "Saving…" : "Continue to my list"}
        </button>
      </form>
    </div>
  );
}
