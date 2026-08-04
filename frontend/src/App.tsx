import { useCallback, useEffect, useState } from "react";
import { AdminDebug } from "./pages/AdminDebug";
import CheckoutPage from "./pages/Checkout";
import Onboarding from "./pages/Onboarding";
import OrderSuccess from "./pages/OrderSuccess";
import ShopHome from "./pages/ShopHome";
import UslHome from "./pages/UslHome";
import WelcomeOnboarding from "./pages/WelcomeOnboarding";
import { api, LocationResponse, UslItemResponse } from "./api/client";
import BottomNav, { NavTab } from "./components/layout/BottomNav";

type AppState =
  | "loading"
  | "welcome"
  | "onboarding"
  | "home"
  | "shop"
  | "checkout"
  | "orderSuccess"
  | "admin";

const ADMIN_DEBUG = import.meta.env.VITE_ADMIN_DEBUG === "true";
const WELCOME_KEY = "usl_welcome_seen";

export default function App() {
  const [state, setState] = useState<AppState>("loading");
  const [location, setLocation] = useState<LocationResponse | null>(null);
  const [checkoutEnabled, setCheckoutEnabled] = useState(false);
  const [uslItems, setUslItems] = useState<UslItemResponse[]>([]);
  const [orderMessage, setOrderMessage] = useState("");
  const [error, setError] = useState("");

  const loadUslMeta = useCallback(async () => {
    try {
      const data = await api.listItems("all");
      setUslItems(data.items);
    } catch {
      setUslItems([]);
    }
  }, []);

  useEffect(() => {
    if (window.location.hash === "#admin" && ADMIN_DEBUG) {
      setState("admin");
      return;
    }

    Promise.all([api.getLocation().catch(() => null), api.getFlags().catch(() => null)]).then(([loc, flags]) => {
      setCheckoutEnabled(flags?.usl_checkout_recommendations ?? false);
      if (!loc) {
        const seenWelcome = localStorage.getItem(WELCOME_KEY);
        setState(seenWelcome ? "onboarding" : "welcome");
        return;
      }
      setLocation(loc);
      loadUslMeta();
      setState("shop");
    });
  }, [loadUslMeta]);

  function handleWelcomeContinue() {
    localStorage.setItem(WELCOME_KEY, "1");
    setState("onboarding");
  }

  function handleOnboardingComplete() {
    api
      .getLocation()
      .then((loc) => {
        setLocation(loc);
        return loadUslMeta().then(() => loc);
      })
      .then(() => setState("home"))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load location"));
    api.getFlags().then((flags) => setCheckoutEnabled(flags?.usl_checkout_recommendations ?? false)).catch(() => {});
  }

  function navigateTab(tab: NavTab) {
    setState(tab === "shop" ? "shop" : "home");
  }

  const showBottomNav = state === "home" || state === "shop";
  const availableCount = uslItems.filter((i) => i.catalog_matches.some((m) => m.availability_status !== "unavailable")).length;
  const uslAvailablePct = uslItems.length === 0 ? 0 : Math.round((availableCount / uslItems.length) * 100);

  if (state === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <p className="text-sm text-on-surface-variant">Loading Blinkit…</p>
      </div>
    );
  }

  if (state === "admin" && ADMIN_DEBUG) {
    return <AdminDebug />;
  }

  return (
    <div className="mx-auto min-h-screen max-w-md bg-surface">
      {error && (
        <p className="bg-error-container px-4 py-2 text-center text-sm text-error">{error}</p>
      )}

      {state === "welcome" && (
        <WelcomeOnboarding onContinue={handleWelcomeContinue} onSkip={() => setState("onboarding")} />
      )}

      {state === "onboarding" && (
        <Onboarding onComplete={handleOnboardingComplete} onBack={() => setState("welcome")} />
      )}

      {state === "home" && location && (
        <UslHome
          location={location}
          onContinueShopping={() => {
            loadUslMeta();
            setState("shop");
          }}
        />
      )}

      {state === "shop" && location && (
        <ShopHome
          location={location}
          checkoutEnabled={checkoutEnabled}
          uslAvailablePct={uslAvailablePct}
          onGoToCheckout={() => setState("checkout")}
          onGoToUsl={() => setState("home")}
        />
      )}

      {state === "checkout" && location && (
        <CheckoutPage
          location={location}
          onBack={() => setState("shop")}
          onOrderPlaced={(msg) => {
            setOrderMessage(msg);
            setState("orderSuccess");
          }}
        />
      )}

      {state === "orderSuccess" && (
        <OrderSuccess
          message={orderMessage}
          onDone={() => {
            loadUslMeta();
            setState("shop");
          }}
        />
      )}

      {showBottomNav && (
        <BottomNav
          active={state === "shop" ? "shop" : "list"}
          onNavigate={navigateTab}
          listHasItems={uslItems.length > 0}
        />
      )}
    </div>
  );
}
