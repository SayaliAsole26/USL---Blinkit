import { FormEvent, useState } from "react";
import { api } from "../api/client";

type Props = {
  onComplete: () => void;
};

export default function Onboarding({ onComplete }: Props) {
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [pincode, setPincode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.setLocation({ city, state, pincode });
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="hero">
        <span className="badge">Step 1</span>
        <h1>Where do you shop?</h1>
        <p>
          USL remembers what you want to buy — across groceries, electronics, pet care, and more.
          We only use your location to check availability later.
        </p>
      </div>

      <form className="card form-card" onSubmit={handleSubmit}>
        <label>
          City
          <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Bangalore" required />
        </label>
        <label>
          State
          <input value={state} onChange={(e) => setState(e.target.value)} placeholder="Karnataka" required />
        </label>
        <label>
          Pincode
          <input
            value={pincode}
            onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="560001"
            inputMode="numeric"
            pattern="\d{6}"
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Saving…" : "Continue to my list"}
        </button>
      </form>
    </div>
  );
}
