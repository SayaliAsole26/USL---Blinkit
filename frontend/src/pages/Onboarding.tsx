import { useState } from "react";
import { api, getApiBaseUrl } from "../api/client";
import Icon from "../components/layout/Icon";
import { DELIVERY_LOCATIONS, DeliveryLocation } from "../data/deliveryLocations";

type Props = {
  onComplete: () => void;
  onBack?: () => void;
};

export default function Onboarding({ onComplete, onBack }: Props) {
  const [selected, setSelected] = useState<DeliveryLocation | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleContinue() {
    if (!selected) return;

    setError("");
    setLoading(true);
    try {
      await api.setLocation({
        city: selected.city,
        state: selected.state,
        pincode: selected.pincode,
      });
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-gray pb-8">
      <header className="sticky top-0 z-40 flex h-14 items-center gap-3 bg-surface px-4">
        {onBack && (
          <button type="button" onClick={onBack} className="active-scale flex h-10 w-10 items-center justify-center rounded-full">
            <Icon name="arrow_back" className="text-primary" />
          </button>
        )}
        <div>
          <h1 className="text-lg font-bold text-primary">Choose delivery location</h1>
          <p className="text-xs text-on-surface-variant">Select a city with catalog coverage</p>
        </div>
      </header>

      <div className="mx-4 mt-6 space-y-4 rounded-2xl bg-surface p-5 card-shadow">
        <p className="text-sm text-on-surface-variant">
          Only locations in our demo dataset are available. Product availability varies by pincode.
        </p>

        <ul className="space-y-3">
          {DELIVERY_LOCATIONS.map((location) => {
            const isSelected = selected?.id === location.id;
            return (
              <li key={location.id}>
                <button
                  type="button"
                  onClick={() => setSelected(location)}
                  className={`flex w-full items-center justify-between rounded-xl border px-4 py-4 text-left transition-all active:scale-[0.99] ${
                    isSelected
                      ? "border-primary bg-primary-container/20 ring-2 ring-primary/30"
                      : "border-border-subtle bg-surface-container-low hover:border-primary/40"
                  }`}
                >
                  <div>
                    <p className="font-semibold text-on-surface">{location.city}</p>
                    <p className="text-sm text-on-surface-variant">
                      {location.state} · {location.pincode}
                    </p>
                    <p className="mt-0.5 text-xs text-on-surface-variant">{location.label}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-xs font-medium text-on-surface-variant">
                      {location.productCount} products
                    </span>
                    {isSelected && <Icon name="check_circle" className="text-primary" />}
                  </div>
                </button>
              </li>
            );
          })}
        </ul>

        {error && (
          <div className="space-y-1 text-sm text-error">
            <p>{error}</p>
            <p className="text-xs text-on-surface-variant">API: {getApiBaseUrl()}</p>
          </div>
        )}

        <button
          type="button"
          onClick={handleContinue}
          disabled={loading || !selected}
          className="h-12 w-full rounded-xl bg-primary-container text-base font-semibold text-on-primary transition-all active:scale-[0.96] disabled:opacity-60"
        >
          {loading ? "Saving…" : selected ? `Continue · ${selected.city} ${selected.pincode}` : "Select a location"}
        </button>
      </div>
    </div>
  );
}
