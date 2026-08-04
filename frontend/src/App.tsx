import { useCallback, useEffect, useState } from "react";
import { AdminDebug } from "./pages/AdminDebug";
import AccountPage from "./pages/AccountPage";
import CategoriesPage from "./pages/CategoriesPage";
import CheckoutPage from "./pages/Checkout";
import Onboarding from "./pages/Onboarding";
import OrderSuccess from "./pages/OrderSuccess";
import OrdersPage from "./pages/OrdersPage";
import ShopHome from "./pages/ShopHome";
import UslHome from "./pages/UslHome";
import WelcomeOnboarding from "./pages/WelcomeOnboarding";
import { api, ensureUserSession, LocationResponse, UslItemResponse, warmupApi } from "./api/client";
import BottomNav, { NavTab } from "./components/layout/BottomNav";

type AppState =
  | "loading"
  | "welcome"
  | "onboarding"
  | "home"
  | "shop"
  | "checkout"
  | "orderSuccess"
  | "categories"
  | "orders"
  | "account"
  | "admin";

const ADMIN_DEBUG = import.meta.env.VITE_ADMIN_DEBUG === "true";
const WELCOME_KEY = "usl_welcome_seen";

export default function App() {
  const [state, setState] = useState<AppState>("loading");
  const [location, setLocation] = useState<LocationResponse | null>(null);
  const [checkoutEnabled, setCheckoutEnabled] = useState(false);
  const [uslItems, setUslItems] = useState<UslItemResponse[]>([]);
  const [orderMessage, setOrderMessage] = useState("");
  const [shopCategory, setShopCategory] = useState("all");
  const [locationReturnState, setLocationReturnState] = useState<AppState>("shop");
  const [changingLocation, setChangingLocation] = useState(false);

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

    ensureUserSession();

    warmupApi().finally(() => {
      Promise.all([api.getLocation().catch(() => null), api.getFlags().catch(() => null)]).then(([loc, flags]) => {
        setCheckoutEnabled(flags?.usl_checkout_recommendations ?? false);
        if (!loc) {
          const seenWelcome = localStorage.getItem(WELCOME_KEY);
          setState(seenWelcome ? "onboarding" : "welcome");
          return;
        }
        setLocation(loc);
        loadUslMeta();
        setState("home");
      });
    });
  }, [loadUslMeta]);

  function handleWelcomeContinue() {
    localStorage.setItem(WELCOME_KEY, "1");
    setChangingLocation(false);
    setState("onboarding");
  }

  function handleOnboardingComplete(saved: LocationResponse) {
    setLocation(saved);
    setChangingLocation(false);
    loadUslMeta().then(() => setState(changingLocation ? locationReturnState : "home"));
    api.getFlags().then((flags) => setCheckoutEnabled(flags?.usl_checkout_recommendations ?? false)).catch(() => {});
  }

  function handleChangeLocation(from: AppState = "shop") {
    setLocationReturnState(from);
    setChangingLocation(true);
    setState("onboarding");
  }

  function navigateTab(tab: NavTab) {
    if (tab === "shop") setState("shop");
    else if (tab === "list") setState("home");
    else if (tab === "categories") setState("categories");
    else if (tab === "orders") setState("orders");
    else if (tab === "account") setState("account");
  }

  function handleSelectCategory(category: string) {
    setShopCategory(category);
    setState("shop");
  }

  const showBottomNav =
    state === "home" ||
    state === "shop" ||
    state === "categories" ||
    state === "orders" ||
    state === "account";

  const navActive: NavTab =
    state === "home"
      ? "list"
      : state === "categories"
        ? "categories"
        : state === "orders"
          ? "orders"
          : state === "account"
            ? "account"
            : "shop";

  const availableCount = uslItems.filter((i) =>
    i.catalog_matches.some((m) => m.availability_status !== "unavailable")
  ).length;
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
      {state === "welcome" && (
        <WelcomeOnboarding onContinue={handleWelcomeContinue} onSkip={() => setState("onboarding")} />
      )}

      {state === "onboarding" && (
        <Onboarding
          onComplete={handleOnboardingComplete}
          onBack={changingLocation ? () => setState(locationReturnState) : () => setState("welcome")}
          changingLocation={changingLocation}
          currentLocation={location}
        />
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
          initialCategory={shopCategory}
          onCategoryApplied={() => setShopCategory("all")}
          onGoToCheckout={() => setState("checkout")}
          onGoToUsl={() => setState("home")}
          onChangeLocation={() => handleChangeLocation("shop")}
        />
      )}

      {state === "categories" && location && (
        <CategoriesPage
          location={location}
          onChangeLocation={() => handleChangeLocation("categories")}
          onSelectCategory={handleSelectCategory}
        />
      )}

      {state === "orders" && location && (
        <OrdersPage
          location={location}
          onChangeLocation={() => handleChangeLocation("orders")}
          onStartShopping={() => setState("shop")}
        />
      )}

      {state === "account" && location && (
        <AccountPage location={location} onChangeLocation={() => handleChangeLocation("account")} />
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
        <BottomNav active={navActive} onNavigate={navigateTab} listHasItems={uslItems.length > 0} />
      )}
    </div>
  );
}
