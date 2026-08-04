import { LocationResponse } from "../../api/client";
import Icon from "./Icon";

type Props = {
  location: LocationResponse;
  onChangeLocation?: () => void;
  compact?: boolean;
};

export default function LocationBanner({ location, onChangeLocation, compact }: Props) {
  return (
    <button
      type="button"
      onClick={onChangeLocation}
      className={`flex items-center gap-2 text-left ${onChangeLocation ? "active:scale-[0.98]" : ""}`}
      disabled={!onChangeLocation}
    >
      <div className={`flex items-center justify-center rounded-full bg-white shadow-sm ${compact ? "h-8 w-8" : "h-10 w-10"}`}>
        <Icon name="location_on" filled className="text-primary" />
      </div>
      <div>
        <span className={`font-bold leading-tight ${compact ? "text-xs" : "text-sm"}`}>Delivering to</span>
        <div className="flex items-center gap-1">
          <span className={`font-extrabold leading-tight ${compact ? "text-sm" : "text-base"}`}>
            {location.pincode} - {location.city}
          </span>
          {onChangeLocation && <Icon name="keyboard_arrow_down" className="text-sm" />}
        </div>
        {!compact && (
          <span className="text-xs text-on-surface-variant">
            {location.state}
          </span>
        )}
      </div>
    </button>
  );
}
