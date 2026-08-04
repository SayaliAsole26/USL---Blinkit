import Icon from "./Icon";

export type NavTab = "shop" | "list" | "categories" | "orders" | "account";

type Props = {
  active: NavTab;
  onNavigate: (tab: NavTab) => void;
  listHasItems?: boolean;
};

export default function BottomNav({ active, onNavigate, listHasItems }: Props) {
  const tabs: Array<{ id: NavTab; icon: string; label: string; filled?: boolean }> = [
    { id: "shop", icon: "home", label: "Home", filled: active === "shop" },
    { id: "categories", icon: "grid_view", label: "Categories", filled: active === "categories" },
    { id: "list", icon: "format_list_bulleted", label: "My List", filled: active === "list" },
    { id: "orders", icon: "receipt_long", label: "Orders", filled: active === "orders" },
    { id: "account", icon: "person", label: "Account", filled: active === "account" },
  ];

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex h-16 w-full items-center justify-around border-t border-border-subtle bg-surface px-2 pb-safe shadow-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onNavigate(tab.id)}
          className={`relative flex flex-col items-center justify-center transition-all active:scale-95 ${
            active === tab.id ? "font-bold text-primary" : "text-on-surface-variant opacity-70"
          }`}
        >
          <Icon name={tab.icon} filled={tab.filled} className="text-2xl" />
          <span className="mt-0.5 text-[11px] font-bold">{tab.label}</span>
          {tab.id === "list" && listHasItems && active !== "list" && (
            <span className="absolute right-0 top-0 h-2 w-2 rounded-full border-2 border-surface bg-error" />
          )}
        </button>
      ))}
    </nav>
  );
}
