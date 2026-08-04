import { AdminDebug } from "./pages/AdminDebug";
import CheckoutPage from "./pages/Checkout";
import { useEffect, useState } from "react";
import { api, LocationResponse } from "./api/client";
import Onboarding from "./pages/Onboarding";
import UslHome from "./pages/UslHome";

type AppState = "loading" | "onboarding" | "home" | "checkout" | "admin";

const ADMIN_DEBUG = import.meta.env.VITE_ADMIN_DEBUG === "true";

export default function App() {
  const [state, setState] = useState<AppState>("loading");
  const [location, setLocation] = useState<LocationResponse | null>(null);
  const [checkoutEnabled, setCheckoutEnabled] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (window.location.hash === "#admin" && ADMIN_DEBUG) {
      setState("admin");
      return;
    }

    Promise.all([api.getLocation().catch(() => null), api.getFlags().catch(() => null)]).then(([loc, flags]) => {
      if (!loc) {
        setState("onboarding");
        return;
      }
      setLocation(loc);
      setCheckoutEnabled(flags?.usl_checkout_recommendations ?? false);
      setState("home");
    });
  }, []);

  function handleOnboardingComplete() {
    api
      .getLocation()
      .then((loc) => {
        setLocation(loc);
        setState("home");
        return api.getFlags();
      })
      .then((flags) => setCheckoutEnabled(flags?.usl_checkout_recommendations ?? false))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load location"));
  }

  if (state === "loading") {
    return (
      <div className="app-shell">
        <p className="muted center">Loading USL…</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <span className="logo">Blinkit USL</span>
        <span className="phase-badge">Phase 3</span>
        {ADMIN_DEBUG && (
          <button type="button" className="btn-ghost" onClick={() => setState(state === "admin" ? "home" : "admin")}>
            {state === "admin" ? "Back to list" : "Match debug"}
          </button>
        )}
      </div>
      {error && <p className="error center">{error}</p>}
      {state === "onboarding" && <Onboarding onComplete={handleOnboardingComplete} />}
      {state === "home" && location && (
        <UslHome
          location={location}
          checkoutEnabled={checkoutEnabled}
          onGoToCheckout={() => setState("checkout")}
        />
      )}
      {state === "checkout" && location && (
        <CheckoutPage location={location} onBack={() => setState("home")} />
      )}
      {state === "admin" && ADMIN_DEBUG && <AdminDebug />}
    </div>
  );
}
