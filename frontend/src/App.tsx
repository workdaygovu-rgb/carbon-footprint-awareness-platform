import { CalculatorForm } from "./components/CalculatorForm";
import { ResultBreakdown } from "./components/ResultBreakdown";
import { InsightsPanel } from "./components/InsightsPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { useFootprint } from "./hooks/useFootprint";

/**
 * Application shell: composes the calculator, results, insights, and history
 * panels around the `useFootprint` hook, which owns all async state.
 */
export default function App() {
  const { result, insights, entries, loading, saving, error, status, calculate, save } =
    useFootprint();

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <header className="app-header">
        <h1>Carbon Footprint Awareness Platform</h1>
        <p>Understand, track, and reduce your carbon footprint.</p>
      </header>

      <main id="main">
        <CalculatorForm onSubmit={calculate} loading={loading} />

        <div role="alert" aria-live="assertive">
          {error && <p className="error">{error}</p>}
        </div>
        <p role="status" className="visually-hidden">
          {status}
        </p>

        {result && (
          <>
            <ResultBreakdown result={result} />
            {insights && <InsightsPanel insights={insights} />}
            <div className="card">
              <button className="btn secondary" onClick={save} disabled={saving} aria-busy={saving}>
                {saving ? "Saving…" : "Save this entry to my history"}
              </button>
            </div>
          </>
        )}

        <HistoryPanel entries={entries} />
      </main>
    </>
  );
}
