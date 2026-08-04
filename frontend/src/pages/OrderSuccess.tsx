import Icon from "../components/layout/Icon";

type Props = {
  message: string;
  onDone: () => void;
};

export default function OrderSuccess({ message, onDone }: Props) {
  return (
    <div className="flex min-h-screen flex-col bg-surface px-4 py-10">
      <div className="mb-10 flex items-center justify-between">
        <span className="text-lg font-bold text-primary">blinkit</span>
        <button type="button" onClick={onDone} className="rounded-full p-2 hover:bg-surface-container-low">
          <Icon name="close" />
        </button>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center text-center">
        <div className="animate-success mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-primary/10">
          <Icon name="check_circle" filled className="text-5xl text-primary-container" />
        </div>
        <h1 className="mb-2 text-2xl font-bold">Order placed!</h1>
        <p className="mb-8 max-w-xs text-sm text-on-surface-variant">{message}</p>
        <p className="mb-8 text-sm text-on-surface-variant">Your order is on the way. USL items marked purchased will sync automatically.</p>
        <button
          type="button"
          onClick={onDone}
          className="h-12 w-full max-w-sm rounded-xl bg-primary-container text-base font-semibold text-on-primary active:scale-[0.96]"
        >
          Back to Home
        </button>
      </div>
    </div>
  );
}
