type Props = {
  name: string;
  filled?: boolean;
  className?: string;
  size?: number;
};

export default function Icon({ name, filled = false, className = "", size }: Props) {
  return (
    <span
      className={`material-symbols-outlined ${filled ? "material-symbols-filled" : ""} ${className}`}
      style={size ? { fontSize: size } : undefined}
      aria-hidden
    >
      {name}
    </span>
  );
}
