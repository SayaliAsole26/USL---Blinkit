import Icon from "./Icon";

export type NavTab = "shop" | "list";

type Props = {
  active: NavTab;
  onNavigate: (tab: NavTab) => void;
  listHasItems?: boolean;
};

export default function BottomNav({ active, onNavigate, listHasItems }: Props) {
  return (
    <nav className="fixed bottom-0 left-0 z-50 flex h-16 w-full items-center justify-around border-t border-border-subtle bg-surface px-2 pb-safe shadow-lg">
      <button
        type="button"
        onClick={() => onNavigate("shop")}
        className={`flex flex-col items-center justify-center transition-all active:scale-95 ${
          active === "shop" ? "font-bold text-primary" : "text-on-surface-variant opacity-70"
        }`}
      >
        <Icon name="home" filled={active === "shop"} className="text-2xl" />
        <span className="mt-0.5 text-[11px] font-bold">Home</span>
      </button>
      <button type="button" className="flex flex-col items-center justify-center text-on-surface-variant opacity-70" disabled>
        <Icon name="grid_view" className="text-2xl" />
        <span className="mt-0.5 text-[11px] font-bold">Categories</span>
      </button>
      <button
        type="button"
        onClick={() => onNavigate("list")}
        className={`relative flex flex-col items-center justify-center transition-all active:scale-95 ${
          active === "list" ? "font-bold text-primary" : "text-on-surface-variant opacity-70"
        }`}
      >
        <Icon name="format_list_bulleted" filled={active === "list"} className="text-2xl" />
        <span className="mt-0.5 text-[11px] font-bold">My List</span>
        {listHasItems && active !== "list" && (
          <span className="absolute right-0 top-0 h-2 w-2 rounded-full border-2 border-surface bg-error" />
        )}
      </button>
      <button type="button" className="flex flex-col items-center justify-center text-on-surface-variant opacity-70" disabled>
        <Icon name="receipt_long" className="text-2xl" />
        <span className="mt-0.5 text-[11px] font-bold">Orders</span>
      </button>
      <button type="button" className="flex flex-col items-center justify-center text-on-surface-variant opacity-70" disabled>
        <Icon name="person" className="text-2xl" />
        <span className="mt-0.5 text-[11px] font-bold">Account</span>
      </button>
    </nav>
  );
}
