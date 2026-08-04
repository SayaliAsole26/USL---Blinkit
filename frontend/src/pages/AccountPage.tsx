import { LocationResponse } from "../api/client";
import { DELIVERY_LOCATIONS } from "../data/deliveryLocations";
import LocationBanner from "../components/layout/LocationBanner";
import Icon from "../components/layout/Icon";

type Props = {
  location: LocationResponse;
  onChangeLocation: () => void;
};

export default function AccountPage({ location, onChangeLocation }: Props) {
  const matched = DELIVERY_LOCATIONS.find((l) => l.pincode === location.pincode);

  return (
    <div className="min-h-screen bg-surface pb-20">
      <header className="sticky top-0 z-40 border-b border-border-subtle bg-surface px-4 py-3">
        <h1 className="text-lg font-bold">Account</h1>
      </header>

      <main className="space-y-4 p-4">
        <section className="rounded-2xl border border-border-subtle bg-surface-container-low p-4">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-container text-xl font-bold text-on-primary">
              {location.city.charAt(0)}
            </div>
            <div>
              <p className="font-bold">Demo User</p>
              <p className="text-sm text-on-surface-variant">Blinkit USL demo account</p>
            </div>
          </div>
          <LocationBanner location={location} onChangeLocation={onChangeLocation} />
          {matched && (
            <p className="mt-2 text-xs text-on-surface-variant">{matched.label}</p>
          )}
        </section>

        <section className="rounded-2xl border border-border-subtle bg-surface-container-low p-4">
          <h2 className="mb-3 text-sm font-bold">Delivery details</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">City</dt>
              <dd className="font-medium">{location.city}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">State</dt>
              <dd className="font-medium">{location.state}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface-variant">Pincode</dt>
              <dd className="font-medium">{location.pincode}</dd>
            </div>
          </dl>
          <button
            type="button"
            onClick={onChangeLocation}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-primary py-3 text-sm font-semibold text-primary active:scale-[0.98]"
          >
            <Icon name="edit_location_alt" />
            Change location
          </button>
        </section>
      </main>
    </div>
  );
}
