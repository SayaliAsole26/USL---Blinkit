import { useMemo, useState } from "react";
import { api, getApiBaseUrl, LocationResponse } from "../api/client";
import Icon from "../components/layout/Icon";
import { DELIVERY_LOCATIONS, DeliveryLocation } from "../data/deliveryLocations";

type Props = {
  onComplete: (location: LocationResponse) => void;
  onBack?: () => void;
  changingLocation?: boolean;
  currentLocation?: LocationResponse | null;
};

export default function Onboarding({ onComplete, onBack, changingLocation, currentLocation }: Props) {
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const currentId = useMemo(
    () => DELIVERY_LOCATIONS.find((l) => l.pincode === currentLocation?.pincode)?.id ?? null,
    [currentLocation?.pincode]
  );

  async function selectLocation(location: DeliveryLocation) {
    if (savingId) return;

    if (changingLocation && currentLocation?.pincode === location.pincode) {
      onComplete(currentLocation);
      return;
    }

    setError("");
    setSavingId(location.id);
    try {
      const saved = await api.setLocation({
        city: location.city,
        state: location.state,
        pincode: location.pincode,
      });
      onComplete(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location");
      setSavingId(null);
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
          <h1 className="text-lg font-bold text-primary">
            {changingLocation ? "Change delivery location" : "Choose delivery location"}
          </h1>
          <p className="text-xs text-on-surface-variant">
            Tap a city to {changingLocation ? "update" : "set"} your delivery pincode
          </p>
        </div>
      </header>

      <div className="mx-4 mt-6 space-y-4 rounded-2xl bg-surface p-5 card-shadow">
        <p className="text-sm text-on-surface-variant">
          Only locations in our demo dataset are available. Product availability varies by pincode.
        </p>

        <ul className="space-y-3">
          {DELIVERY_LOCATIONS.map((location) => {
            const isCurrent = currentId === location.id;
            const isSaving = savingId === location.id;
            const isDisabled = savingId !== null && !isSaving;

            return (
              <li key={location.id}>
                <button
                  type="button"
                  disabled={isDisabled}
                  onClick={() => selectLocation(location)}
                  className={`flex w-full items-center justify-between rounded-xl border px-4 py-4 text-left transition-all active:scale-[0.99] disabled:opacity-50 ${
                    isSaving
                      ? "border-primary bg-primary-container/30 ring-2 ring-primary/40"
                      : isCurrent
                        ? "border-primary/60 bg-primary-container/10"
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
                    {isSaving && (
                      <span className="text-xs font-medium text-primary">Saving…</span>
                    )}
                    {!isSaving && isCurrent && (
                      <Icon name="check_circle" className="text-primary" />
                    )}
                    {!isSaving && !isCurrent && (
                      <Icon name="chevron_right" className="text-on-surface-variant" />
                    )}
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
      </div>
    </div>
  );
}
