import { LocationResponse } from "../api/client";
import LocationBanner from "../components/layout/LocationBanner";
import Icon from "../components/layout/Icon";

type Props = {
  location: LocationResponse;
  onChangeLocation: () => void;
  onStartShopping: () => void;
};

export default function OrdersPage({ location, onChangeLocation, onStartShopping }: Props) {
  return (
    <div className="min-h-screen bg-surface pb-20">
      <header className="sticky top-0 z-40 border-b border-border-subtle bg-surface px-4 py-3">
        <h1 className="mb-3 text-lg font-bold">Orders</h1>
        <LocationBanner location={location} onChangeLocation={onChangeLocation} compact />
      </header>

      <main className="flex flex-col items-center px-4 pt-12 text-center">
        <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-low">
          <Icon name="receipt_long" className="text-4xl text-on-surface-variant" />
        </div>
        <h2 className="text-lg font-bold">No orders yet</h2>
        <p className="mt-2 max-w-xs text-sm text-on-surface-variant">
          Orders placed from {location.city} ({location.pincode}) will appear here after checkout.
        </p>
        <button
          type="button"
          onClick={onStartShopping}
          className="mt-6 rounded-xl bg-primary-container px-6 py-3 text-sm font-semibold text-on-primary active:scale-95"
        >
          Start shopping
        </button>
      </main>
    </div>
  );
}
