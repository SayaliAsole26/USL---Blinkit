import Icon from "../components/layout/Icon";

type Props = {
  onContinue: () => void;
  onSkip?: () => void;
};

export default function WelcomeOnboarding({ onContinue, onSkip }: Props) {
  return (
    <div className="flex min-h-screen flex-col items-center overflow-hidden bg-background text-on-surface">
      <header className="fixed top-0 z-50 flex h-14 w-full items-center justify-between bg-surface px-4">
        <span className="text-lg font-bold tracking-tighter text-primary">blinkit</span>
        <Icon name="notifications" className="text-on-surface-variant" />
      </header>

      <main className="flex w-full max-w-md flex-1 flex-col items-center px-4 pb-32 pt-20">
        <div className="relative mb-4 flex aspect-square max-h-[360px] w-full items-center justify-center">
          <div className="absolute h-48 w-48 rounded-full bg-primary/10 blur-3xl" />
          <div className="relative z-10 flex h-60 w-48 -rotate-2 flex-col gap-3 rounded-xl border border-border-subtle bg-white p-4 card-shadow">
            <div className="absolute -top-3 left-1/2 flex -translate-x-1/2 gap-1">
              <div className="h-6 w-6 rounded-full border-4 border-background bg-surface-container-high" />
              <div className="h-6 w-6 rounded-full border-4 border-background bg-surface-container-high" />
            </div>
            <div className="h-2 w-full rounded-full bg-surface-gray" />
            {[true, true, false, false, false].map((checked, i) => (
              <div key={i} className="flex items-center gap-2">
                <div
                  className={`flex h-4 w-4 items-center justify-center rounded border-2 ${
                    checked ? "border-primary" : "border-outline-variant"
                  }`}
                >
                  {checked && <Icon name="check" className="text-[12px] text-primary" />}
                </div>
                <div className={`h-3 rounded-full bg-surface-container-low ${i > 2 ? "w-1/2" : "w-full"}`} />
              </div>
            ))}
          </div>
          <div className="absolute right-6 top-2 animate-pulse text-ai-text">
            <Icon name="auto_awesome" filled size={32} />
          </div>
        </div>

        <div className="space-y-2 px-4 text-center">
          <h1 className="text-2xl font-bold tracking-tight">Never forget anything you need.</h1>
          <p className="text-sm leading-relaxed text-on-surface-variant">
            Add everything you may buy online — from groceries to skincare, electronics, fashion and more. We'll
            remind you whenever Blinkit can deliver it.
          </p>
        </div>
      </main>

      <footer className="fixed bottom-0 z-50 flex w-full flex-col gap-4 bg-white/80 px-4 pb-10 pt-4 backdrop-blur-lg">
        <div className="-mt-8 mb-2 flex justify-center">
          <div className="flex items-center gap-1.5 rounded-full border border-ai-text/10 bg-ai-surface px-3 py-1">
            <Icon name="auto_awesome" filled size={14} className="text-ai-text" />
            <span className="text-[11px] font-bold text-ai-text">AI-POWERED CATEGORIZATION</span>
          </div>
        </div>
        <button
          type="button"
          onClick={onContinue}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-primary-container text-base font-semibold text-on-primary shadow-lg shadow-primary/20 transition-all active:scale-[0.96]"
        >
          Create My Universal List
        </button>
        {onSkip && (
          <button type="button" onClick={onSkip} className="rounded-lg py-2 text-sm font-medium text-on-surface-variant">
            Maybe Later
          </button>
        )}
      </footer>
    </div>
  );
}
