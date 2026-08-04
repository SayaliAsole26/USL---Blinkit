import Icon from "../layout/Icon";

type Props = {
  label?: string;
  className?: string;
};

export default function AiPill({ label = "AI Categorized", className = "" }: Props) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full border border-ai-text/10 bg-ai-surface px-3 py-1.5 text-ai-text ${className}`}
    >
      <Icon name="auto_awesome" filled size={14} />
      <span className="text-[11px] font-bold uppercase tracking-wider">{label}</span>
    </div>
  );
}
