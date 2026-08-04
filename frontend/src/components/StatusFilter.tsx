import { StatusFilter, UslItemResponse } from "../api/client";

type Props = {
  value: StatusFilter;
  onChange: (value: StatusFilter) => void;
};

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "purchased", label: "Purchased" },
  { value: "all", label: "All" },
];

export default function StatusFilterBar({ value, onChange }: Props) {
  return (
    <div className="filter-bar">
      {FILTERS.map((filter) => (
        <button
          key={filter.value}
          type="button"
          className={value === filter.value ? "filter active" : "filter"}
          onClick={() => onChange(filter.value)}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}

export function formatStatus(status: UslItemResponse["status"]): string {
  return status.replace(/_/g, " ");
}
