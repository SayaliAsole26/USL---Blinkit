import Icon from "../layout/Icon";

type Props = {
  score: number;
  hint?: string;
  variant?: "ai" | "primary";
};

export default function CompletionScore({ score, hint, variant = "ai" }: Props) {
  const pct = Math.min(100, Math.max(0, score));
  const scoreColor = variant === "ai" ? "text-ai-text" : "text-primary";
  const barColor = variant === "ai" ? "bg-primary" : "bg-primary";

  return (
    <div className="relative overflow-hidden rounded-xl border border-border-subtle bg-surface-container-lowest p-4 card-shadow">
      {variant === "ai" && (
        <div className="absolute -right-16 -top-16 h-32 w-32 rounded-full bg-ai-surface opacity-50 blur-3xl" />
      )}
      <div className="relative z-10 flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-on-surface">Shopping Completion Score</h3>
        <span className={`text-lg font-semibold ${scoreColor}`}>{pct}%</span>
      </div>
      <div className="relative z-10 mb-3 h-2 w-full overflow-hidden rounded-full bg-border-subtle">
        <div className={`h-full rounded-full transition-all duration-700 ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      {hint && (
        <p className="relative z-10 flex items-center gap-2 text-xs text-on-surface-variant">
          {variant === "primary" && <Icon name="lightbulb" filled className="text-primary text-lg" />}
          {hint}
        </p>
      )}
    </div>
  );
}
